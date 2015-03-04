import base64
import gc
import os
import time
import email.utils


class ResumeAttachmentHelper:
  def __init__(s, service):
    s.service = service


  def get_msg_ids_with_attachments(s, user_id):
    search_query = 'subject:resume AND has:attachment'
    response = s.service.users().messages().list(
        userId=user_id, q=search_query).execute()
    print response

    if 'messages' in response:
      for m in response['messages']:
        yield m['id']

    while 'nextPageToken' in response:
      page_token = response['nextPageToken']
      response = s.service.users().messages().list(
          userId=user_id, q=search_query, pageToken=page_token).execute()
      for m in response['messages']:
        yield m['id']


  def get_header_dict(s, message_resource):
    if 'payload' in message_resource:
      if 'headers' in message_resource['payload']:
        headers = message_resource['payload']['headers']
        return dict((h['name'], h['value']) for h in headers)
    return {}


  def is_resume_extension(s, ext):
    return ext.lower() in {'.pdf', '.doc', '.docx', '.gdoc'}


  def get_attachments(s, message_resource):
    msg_id = message_resource['id']
    if 'payload' in message_resource:
      if 'parts' in message_resource['payload']:
        parts = message_resource['payload']['parts']
        for part in parts:
          if 'filename' in part:
            filename = part['filename']
          if 'body' in part:
            if 'attachmentId' in part['body']:
              attachment_id = part['body']['attachmentId']
          if filename and attachment_id:
            yield {
                'filename': filename,
                'msg_id': msg_id,
                'attachment_id': attachment_id
            }


  def get_msg_attribs(s, user_id, msg_id):
    response = s.service.users().messages().get(
        id=msg_id, userId=user_id).execute()
    print response
    header_dict = s.get_header_dict(response)

    if 'Date' in header_dict:
      date = int(time.mktime(email.utils.parsedate(header_dict['Date'])))

    if 'From' in header_dict:
      sender = header_dict['From']
      if not '<' in sender:
        sender_name = sender
      else:
        sender_name, _ = sender.split('<')
        sender_name = sender_name.strip()

    for attachment in s.get_attachments(response):
      if date and sender_name:
        attachment.update({
            'timestamp': date,
            'sender': sender_name})
        yield attachment


  def get_attachment_data(s, user_id, msg_id, attachment_id):
    response = s.service.users().messages().attachments().get(
        userId=user_id, messageId=msg_id, id=attachment_id).execute()
    print response
    data = base64.urlsafe_b64decode(response['data'].encode('UTF-8'))
    return data


  def get_filename_for_attachment(s, attachment):
    timestamp = attachment['timestamp']
    filename = attachment['filename']
    _, ext = os.path.splitext(filename)
    sender = attachment['sender']
    return sender + '.' + str(timestamp) + ext


  def resumes_to_zip(s, user_id, zipfile):
    for msg_id in s.get_msg_ids_with_attachments(user_id):
      for attachment in s.get_msg_attribs(user_id, msg_id):
        filename = attachment['filename']
        _, ext = os.path.splitext(filename)
        if s.is_resume_extension(ext):
          better_filename = s.get_filename_for_attachment(attachment)
          attachment_id = attachment['attachment_id']
          zipfile.writestr(
              better_filename,
              s.get_attachment_data(user_id, msg_id, attachment_id))
          gc.collect()
