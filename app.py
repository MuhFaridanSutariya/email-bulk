import streamlit as st
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
import pandas as pd
import streamlit.components.v1 as components

# Function to send an email
def send_email(sender_email, password, smtp_server, port, recipient_emails, subject, html_content):
    try:
        message = MIMEMultipart("alternative")
        message['Subject'] = subject
        message['From'] = sender_email
        message['To'] = ", ".join(recipient_emails)

        html_part = MIMEText(html_content, 'html') 
        message.attach(html_part)

        smtp = smtplib.SMTP(smtp_server, port)
        smtp.starttls() 
        smtp.login(sender_email, password)

        smtp.sendmail(sender_email, recipient_emails, message.as_string())
        smtp.quit()
        
        return True, "Email sent successfully!"
    except Exception as e:
        return False, str(e)

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

    # Step 1: Enter API URL
    st.subheader("Step 1: Enter API URL")
    api_url = st.text_input("Enter your API request URL")

    records_json = None
    if api_url:
        records_json = get_records(api_url)

    # If records are available, proceed with data processing
    if records_json and 'data' in records_json:
        records = records_json['data']
        field_labels = records_json.get('field_labels', {})

        # Convert records into DataFrame for easier manipulation
        df = pd.DataFrame(records)
        df = df.drop(columns=['ROW_ID'], errors='ignore')
        df = df.rename(columns=field_labels)

        # Step 2: Complete Data Preview
        st.subheader("Step 2: Complete Data Preview")
        st.dataframe(df)

        # Select category field for filtering
        all_fields = df.columns.tolist()
        category_field = st.selectbox("Select Category Field for Filtering", all_fields)
        unique_categories = df[category_field].dropna().unique().tolist()
        selected_category = st.selectbox("Filter by Category", unique_categories)

        # Filter the DataFrame based on selected category
        filtered_df = df[df[category_field] == selected_category]
        st.subheader("Filtered Data Preview")
        st.dataframe(filtered_df)

        # Step 3: Compose Your Email
        subject = st.text_input("Email Subject")

        tinymce_html = """
        <textarea id="tinymce_editor">Hi {nama},</textarea>
        <script src="https://cdn.tiny.cloud/1/6l6r7bnmos34yfj1tvagp8il2afg7gljk99plswhkp4t1ers/tinymce/5/tinymce.min.js" referrerpolicy="origin"></script>
        <script>
        tinymce.init({
            selector: '#tinymce_editor',
            menubar: false,
            plugins: 'lists link image preview',
            toolbar: 'bold italic underline | bullist numlist | alignleft aligncenter alignright alignjustify | link image',
            setup: function (editor) {
                editor.on('change', function () {
                    tinymce.triggerSave();
                });
            }
        });

        // Kirim konten HTML ke server Flask saat save
        function saveContentToServer() {
            var content = tinymce.get('tinymce_editor').getContent();
            fetch("https://flask-production-8874.up.railway.app/save-email", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({ content: content })
            })
            .then(response => response.json())
            .then(data => {
                alert(data.message || "Content saved successfully");
            })
            .catch(error => {
                console.error('Error:', error);
            });
        }
        </script>
        <button onclick="saveContentToServer()">Save Body Email</button>
        """
        
        components.html(tinymce_html, height=300)

        # Step 4: Send Email
        st.subheader("Step 4: Send Email")
        sender_email = st.text_input("Your Email Address")
        password = st.text_input("Password", type='password')
        smtp_server = st.text_input("SMTP Server", "smtp.gmail.com")
        port = st.number_input("Port", min_value=1, max_value=65535, value=587)

        # Choose recipient field
        email_field = st.selectbox("Select Email Field", all_fields)
        recipient_choice = st.radio("Choose Recipient Type", ["Filtered by Category", "All Emails"])

        # Select emails based on user choice
        if recipient_choice == "Filtered by Category":
            emails = filtered_df[email_field].dropna().tolist()
        else:
            emails = df[email_field].dropna().tolist()

        manual_emails = st.text_area("Enter Emails Manually (one per line)", height=100)
        manual_emails_list = [email.strip() for email in manual_emails.splitlines() if email.strip()]
        recipient_emails = list(set(emails + manual_emails_list))

        if st.button("Send Email"):
            if recipient_emails and subject:
                try: 
                    with open("/mount/src/email-bulk/temp_email_content.txt", "r") as file:
                        html_content = file.read()

                    for email in recipient_emails:
                        if email in df[email_field].values:
                            row = df[df[email_field] == email].iloc[0].to_dict()
                        else:
                            row = {field: "" for field in all_fields}

                        formatted_content = html_content.format(**row)

                        success, feedback = send_email(
                            sender_email, password, smtp_server, port, [email], subject, formatted_content
                        )
                        if success:
                            st.success(f"Email sent to {email} successfully!")
                        else:
                            st.error(f"Failed to send email to {email}: {feedback}")
                except Exception as e:
                    st.error(f"Error reading saved content: {str(e)}")
            else:
                st.error("Please fill in all fields.")

if __name__ == "__main__":
    main()
