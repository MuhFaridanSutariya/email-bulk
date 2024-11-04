import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import pandas as pd

# Function to send an email
def send_email(sender_email, password, smtp_server, port, recipient_emails, subject, html_content):
    try:
        # Create a multipart email
        message = MIMEMultipart("alternative")
        message['Subject'] = subject
        message['From'] = sender_email
        message['To'] = ", ".join(recipient_emails)

        # Attach the HTML content
        html_part = MIMEText(html_content, 'html')
        message.attach(html_part)

        # Connect to the SMTP server
        smtp = smtplib.SMTP(smtp_server, port)
        smtp.starttls()  # Use TLS
        smtp.login(sender_email, password)

        # Send the email
        smtp.sendmail(sender_email, recipient_emails, message.as_string())
        smtp.quit()
        
        return True, "Email sent successfully!"
    except Exception as e:
        return False, str(e)

# Function to get records from API
def get_records(api_url):
    response = requests.get(api_url)
    
    if response.status_code == 200:
        st.write("API request successful.")
        try:
            records_json = response.json()
            if records_json:
                return records_json
            else:
                st.write("No records found.")
        except ValueError:
            st.error("Failed to parse JSON response.")
    else:
        st.error(f"API request failed with status code {response.status_code}.")
    return None

def main():
    st.title("Email Sender Application")

    # Phase 1: Input API URL
    st.subheader("Step 1: Enter API URL")
    api_url = st.text_input("Enter your API request URL")

    records_json = None
    if api_url:
        records_json = get_records(api_url)

    # Phase 2: Select Fields for Email and Category
    if records_json and 'data' in records_json:
        records = records_json['data']
        field_labels = records_json.get('field_labels', {})

        # Convert records to DataFrame
        df = pd.DataFrame(records)

        # Drop ROW_ID if it exists
        df = df.drop(columns=['ROW_ID'], errors='ignore')

        # Rename columns based on field labels
        df = df.rename(columns=field_labels)

        # Display DataFrame and select fields
        st.subheader("Step 2: Select Fields for Email and Category")
        
        # Select email field
        email_field = st.selectbox("Select Email Field", df.columns.tolist())
        
        # Select category field (excluding the selected email field)
        category_field_options = [col for col in df.columns.tolist() if col != email_field]
        category_field = st.selectbox("Select Category Field", category_field_options)

        # Get lists of emails and categories
        emails = df[email_field].tolist()
        categories = df[category_field].tolist()

        # Create a mapping between categories and emails
        category_data = {}
        for email, category in zip(emails, categories):
            if category not in category_data:
                category_data[category] = []
            category_data[category].append(email)

        # Display email preview
        st.subheader("Preview Emails")
        st.table(df[[email_field, category_field]])

        # Phase 3: Email Form
        st.subheader("Step 3: Send Email")
        sender_email = st.text_input("Your Email Address")
        password = st.text_input("Password", type='password')
        smtp_server = st.text_input("SMTP Server", "smtp-mail.outlook.com")
        port = st.number_input("Port", min_value=1, max_value=65535, value=587)

        # Input for manually entered emails
        manual_emails = st.text_area("Enter Emails Manually (one per line)", height=100)

        # Convert the manual emails input into a list
        manual_emails_list = [email.strip() for email in manual_emails.splitlines() if email.strip()]

        recipient_type = st.radio("Choose Recipient Type", ["By Category", "All Emails"])

        recipient_emails = []

        if recipient_type == "By Category":
            selected_category = st.selectbox("Select Category", list(category_data.keys()))
            recipient_emails = category_data[selected_category]
            st.table(recipient_emails)  # Display emails in a table

        elif recipient_type == "All Emails":
            recipient_emails = emails
            st.table(recipient_emails)  # Display all emails in a table

        # Combine manual emails with the selected recipient emails
        recipient_emails = list(set(recipient_emails + manual_emails_list))  # Remove duplicates

        subject = st.text_input("Subject")
        html_content = st.text_area("HTML Content")

        if st.button("Send Email"):
            if recipient_emails and subject and html_content:
                success, feedback = send_email(sender_email, password, smtp_server, port, recipient_emails, subject, html_content)
                if success:
                    st.success(feedback)
                else:
                    st.error(f"Failed to send email: {feedback}")
            else:
                st.error("Please fill in all fields.")

if __name__ == "__main__":
    main()
