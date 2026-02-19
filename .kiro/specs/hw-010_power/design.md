# HW Power Design (hw-010)

## Block diagram
(ASCIIでもOK)

## Design Items

### HW-010-DSN-001 USB-C Input (RevA)
ID: HW-010-DSN-001  
Satisfies: HW-010-RQ-001  

Use USB-C receptacle with 5.1k pull-downs on CC pins to request 5V default current.

Rationale:
- RevA focuses on speed; PD negotiation is deferred.

### HW-010-DSN-002 Protection strategy
ID: HW-010-DSN-002  
Satisfies: HW-010-RQ-002  

Use polyfuse + ideal diode OR load switch (TBD after parts check).

Open questions:
- peak current at startup
- thermal derating
