# HotelOS deployment

## GitHub
Upload this project to a GitHub repository. Do not upload `.env` or production passwords.

## Render
Create a Web Service from the GitHub repository.

- Build: `pip install -r requirements.txt`
- Start: `gunicorn --workers 1 --timeout 120 wsgi:app`
- Plan: Free

Set these environment variables in Render:

- `MYSQL_HOST`
- `MYSQL_PORT` (usually `3306`)
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE`
- `MYSQL_SSL` (`true` for hosted MySQL such as Aiven)
- `SECRET_KEY`
- `ADMIN_PASSWORD`
- `STAFF_PASSWORD`

The MySQL database must already exist and the database user must have permission to create/alter the application's tables.

## Permanent guest history
The application keeps active bookings in `guest` and permanent history in `permanent_guest`. Checkout updates the permanent record to `Checked Out` and removes only the active `guest` record so the room becomes available.
