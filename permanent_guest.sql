-- Run this migration when init_db() is not run automatically.
-- It uses the existing hotel database; it does not create a second database.

CREATE TABLE IF NOT EXISTS permanent_guest (
    permanent_guest_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
    original_guest_id INT NULL,
    nameofguest VARCHAR(50),
    type_of_room VARCHAR(20),
    noofdays INT,
    cidate DATE,
    codate DATE,
    room_no INT,
    source_of_booking VARCHAR(10),
    netpay DECIMAL(12,2),
    booking_token VARCHAR(64) NULL,
    booking_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    checkout_at DATETIME NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'Booked',
    PRIMARY KEY (permanent_guest_id),
    UNIQUE KEY uq_permanent_guest_booking_token (booking_token),
    KEY idx_permanent_guest_original_id (original_guest_id)
);

-- Backfill active bookings already present in guest.
INSERT INTO permanent_guest
    (original_guest_id, nameofguest, type_of_room, noofdays, cidate, codate,
     room_no, source_of_booking, netpay, booking_token, status)
SELECT g.guestid, g.nameofguest, g.type_of_room, g.noofdays, g.cidate, g.codate,
       g.room_no, g.source_of_booking, g.netpay,
       CONCAT('legacy-', g.guestid), 'Booked'
FROM guest AS g
LEFT JOIN permanent_guest AS p
    ON p.booking_token = CONCAT('legacy-', g.guestid)
WHERE p.permanent_guest_id IS NULL;
