# 971town

A social network built around retail, focusing on cataloging products being sold in physical retail stores in Dubai.

## Features

- User authentication via phone number verification
- Brand and store management
- Product catalog with media support
- Store location mapping
- User reporting system
- Admin management interface

## Prerequisites

- Python 3.11
- PostgreSQL
- AWS Account (for S3 media storage)
- Twilio Account (for phone verification)

## Setup

1. Clone the repository
2. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

3. Set up environment variables:

    ```bash
    cp .env.example .env
    ```

4. Edit the `.env` file with your configuration:

    - Database credentials
    - AWS credentials and S3 bucket information
    - Twilio credentials
    - Other configuration options

5. Initialize the database:

    ```bash
    # Run the SQL schema
    psql -U your_db_user -d your_db_name -f app/db/schema_full.sql
    ```

6. Start the development server:

    ```bash
    flask run
    ```

## Environment Variables

The following environment variables need to be set in your `.env` file:

### Flask Configuration

- `FLASK_APP`: Entry point of the application
- `FLASK_DEBUG`: Enable/disable debug mode
- `FLASK_RUN_HOST`: Host to run the application on
- `FLASK_RUN_PORT`: Port to run the application on

### Database Configuration

- `DATABASE_NAME`: PostgreSQL database name
- `DATABASE_USER`: Database user
- `AWS_EC2_PROD_DATABASE_HOST`: Production database host
- `AWS_EC2_PROD_PASSWORD`: Production database password

### AWS Configuration

- `AWS_ACCESS_KEY_ID`: AWS access key
- `AWS_SECRET_ACCESS_KEY`: AWS secret key
- `AWS_REGION`: AWS region for services
- `AWS_S3_MEDIA_BUCKET_NAME`: S3 bucket for media storage

### Twilio Configuration

- `TWILIO_ACCOUNT_SID`: Twilio account SID
- `TWILIO_AUTH_TOKEN`: Twilio authentication token

### Testing Configuration (Development Only)

- `TESTING_OTP`: Static OTP for testing
- `TESTING_PHONE_NUMBER`: Test phone number

## License

This project is licensed under the terms specified in the LICENSE file.

## Author

Created by Ali Mahouk.
