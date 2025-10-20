# Routes API pour la gestion des tickets
# Endpoints pour générer, vérifier et marquer les tickets

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from datetime import datetime
import json
from app.core.database import get_db
from app.models.ticket import Ticket, TicketStatus
from app.models.reservation import Reservation, PaymentStatus
from app.models.schedule import Schedule
from app.models.route import Route
from app.models.agency import Agency
from app.schemas.ticket import TicketGenerate, TicketResponse, TicketVerifyRequest, TicketVerifyResponse
from app.services.crypto import CryptoService
from app.services.pdf import PDFService

router = APIRouter(prefix="/tickets", tags=["Tickets"])

@router.post("/generate", response_model=TicketResponse, status_code=201)
def generate_ticket(ticket_data: TicketGenerate, db: Session = Depends(get_db)):
    reservation = db.query(Reservation).filter(Reservation.id == ticket_data.reservation_id).first()
    if not reservation:
        raise HTTPException(status_code=404, detail="Réservation non trouvée")
    
    if reservation.payment_status != PaymentStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Paiement non effectué")
    
    schedule = db.query(Schedule).filter(Schedule.id == reservation.schedule_id).first()
    if not schedule:
        raise HTTPException(status_code=404, detail="Horaire non trouvé")
    
    route = db.query(Route).filter(Route.id == schedule.route_id).first()
    if not route:
        raise HTTPException(status_code=404, detail="Itinéraire non trouvé")
    
    agency = db.query(Agency).filter(Agency.id == route.agency_id).first()
    if not agency:
        raise HTTPException(status_code=404, detail="Agence non trouvée")
    
    if not agency.public_key or not agency.private_key:
        private_key, public_key = CryptoService.generate_keypair()
        agency.public_key = public_key
        agency.private_key = private_key   
        db.commit()
    else:
        public_key = agency.public_key
        private_key = agency.private_key   

    payload = {
        "ticket_id": str(ticket_data.reservation_id),
        "agency_id": str(agency.id),
        "departure": schedule.departure_time.isoformat(),
        "origin": route.origin,
        "destination": route.destination,
        "passenger": reservation.passenger_info,
        "price": float(schedule.price),
        "issued_at": datetime.utcnow().isoformat(),
        "expires_at": schedule.departure_time.isoformat()
    }
    
    if private_key:
        signature = CryptoService.sign_payload(payload, private_key)
    else:
        raise HTTPException(status_code=500, detail="Clé privée non disponible")
    
    db_ticket = Ticket(
        reservation_id=ticket_data.reservation_id,
        payload=json.dumps(payload),
        signature=signature,
        public_key=public_key,
        status=TicketStatus.VALID,
        expires_at=schedule.departure_time
    )
    
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

@router.get("/{ticket_id}/pdf")
def download_ticket_pdf(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    
    reservation = db.query(Reservation).filter(Reservation.id == ticket.reservation_id).first()
    schedule = db.query(Schedule).filter(Schedule.id == reservation.schedule_id).first()
    route = db.query(Route).filter(Route.id == schedule.route_id).first()
    agency = db.query(Agency).filter(Agency.id == route.agency_id).first()
    
    payload_dict = json.loads(ticket.payload)
    
    pdf_data = {
        "ticket_id": str(ticket.id),
        "agency_name": agency.name,
        "origin": route.origin,
        "destination": route.destination,
        "departure": schedule.departure_time.strftime("%d/%m/%Y %H:%M"),
        "price": reservation.total_amount,
        "passenger": payload_dict.get("passenger", {}),
        "payload": ticket.payload,
        "seat_number": reservation.seat_number,
        "signature": ticket.signature,
        "public_key": ticket.public_key
    }
    
    pdf_buffer = PDFService.generate_ticket_pdf(pdf_data)
    
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=ticket_{ticket.id}.pdf"
        }
    )

@router.post("/verify", response_model=TicketVerifyResponse)
def verify_ticket(verify_data: TicketVerifyRequest, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == verify_data.ticket_id).first()
    if not ticket:
        return TicketVerifyResponse(
            valid=False,
            status="not_found",
            message="Ticket non trouvé"
        )
    
    is_valid = CryptoService.verify_signature(
        verify_data.payload,
        verify_data.signature,
        verify_data.public_key
    )
    
    if not is_valid:
        return TicketVerifyResponse(
            valid=False,
            status="invalid_signature",
            message="Signature invalide"
        )
    
    if ticket.status == TicketStatus.USED:
        return TicketVerifyResponse(
            valid=False,
            status="used",
            message="Ticket déjà utilisé"
        )
    
    if ticket.status == TicketStatus.EXPIRED or ticket.expires_at < datetime.utcnow():
        return TicketVerifyResponse(
            valid=False,
            status="expired",
            message="Ticket expiré"
        )
    
    return TicketVerifyResponse(
        valid=True,
        status="valid",
        message="Ticket valide"
    )

@router.post("/{ticket_id}/mark-used")
def mark_ticket_used(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    
    if ticket.status == TicketStatus.USED:
        raise HTTPException(status_code=400, detail="Ticket déjà utilisé")
    
    ticket.status = TicketStatus.USED
    db.commit()
    
    return {"message": "Ticket marqué comme utilisé", "ticket_id": str(ticket.id)}

@router.get("/{ticket_id}", response_model=TicketResponse)
def get_ticket(ticket_id: str, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket non trouvé")
    return ticket

@router.get("/scanned/history")
def get_scanned_tickets(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    tickets = db.query(Ticket).filter(Ticket.status == TicketStatus.USED).order_by(Ticket.updated_at.desc()).offset(skip).limit(limit).all()
    
    result = []
    for ticket in tickets:
        reservation = db.query(Reservation).filter(Reservation.id == ticket.reservation_id).first()
        schedule = db.query(Schedule).filter(Schedule.id == reservation.schedule_id).first()
        route = db.query(Route).filter(Route.id == schedule.route_id).first()
        agency = db.query(Agency).filter(Agency.id == route.agency_id).first()
        
        payload = json.loads(ticket.payload)
        
        result.append({
            "ticket_id": str(ticket.id),
            "passenger": payload.get("passenger"),
            "origin": route.origin,
            "destination": route.destination,
            "departure": schedule.departure_time,
            "agency": agency.name,
            "seat_number": reservation.seat_number,
            "scanned_at": ticket.updated_at,
            "status": ticket.status
        })
    
    return {
        "total": len(result),
        "tickets": result
    }