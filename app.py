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
        html_part = MIMEText(html_content, 'plain')
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

    st.subheader("Step 1: Enter API URL")
    api_url = st.text_input("Enter your API request URL")

    records_json = None
    if api_url:
        records_json = get_records(api_url)

    if records_json and 'data' in records_json:
        records = records_json['data']
        field_labels = records_json.get('field_labels', {})

        df = pd.DataFrame(records)

        df = df.drop(columns=['ROW_ID'], errors='ignore')

        df = df.rename(columns=field_labels)

        st.subheader("Step 2: Complete Data Preview")
        st.dataframe(df)

        all_fields = df.columns.tolist()

        category_field = st.selectbox("Select Category Field for Filtering", all_fields)
        unique_categories = df[category_field].dropna().unique().tolist()
        selected_category = st.selectbox("Filter by Category", unique_categories)

        filtered_df = df[df[category_field] == selected_category]

        st.subheader("Filtered Data Preview")
        st.dataframe(filtered_df)

        subject = st.text_input("Email Subject")
        html_content_template = st.text_area("Email Content (Use {field_name} for placeholders)", 
                                             "Hi {nama},\n\nSelamat anda mendapatkan pulsa Rp. 5000 {category}")

        st.subheader("Step 3: Send Email")
        sender_email = st.text_input("Your Email Address")
        password = st.text_input("Password", type='password')
        smtp_server = st.text_input("SMTP Server", "smtp-mail.outlook.com")
        port = st.number_input("Port", min_value=1, max_value=65535, value=587)

        email_field = st.selectbox("Select Email Field", all_fields)

        recipient_choice = st.radio("Choose Recipient Type", ["Filtered by Category", "All Emails"])

        if recipient_choice == "Filtered by Category":
            emails = filtered_df[email_field].dropna().tolist()  # Remove NaN values if any
        else:
            emails = df[email_field].dropna().tolist()  # Use all emails

        manual_emails = st.text_area("Enter Emails Manually (one per line)", height=100)
        manual_emails_list = [email.strip() for email in manual_emails.splitlines() if email.strip()]
        recipient_emails = list(set(emails + manual_emails_list)) 

        if st.button("Send Email"):
            if recipient_emails and subject and html_content_template:
                for email in recipient_emails:
                    if email in df[email_field].values:
                        row = df[df[email_field] == email].iloc[0].to_dict()
                    else:
                        row = {field: "" for field in all_fields}

                    html_content = html_content_template.format(**row)

                    success, feedback = send_email(
                        sender_email, password, smtp_server, port, [email], subject, html_content
                    )
                    if success:
                        st.success(f"Email sent to {email} successfully!")
                    else:
                        st.error(f"Failed to send email to {email}: {feedback}")
            else:
                st.error("Please fill in all fields.")

if __name__ == "__main__":
    main()
