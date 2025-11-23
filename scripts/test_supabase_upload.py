#!/usr/bin/env python3
r"""Quick test script to verify Supabase Storage upload using service role key.

Run:
    .\env\Scripts\Activate.ps1
    python scripts\test_supabase_upload.py

It will upload a small text file to the `training_certificates` bucket (or
`SUPABASE_CERT_BUCKET` if set) and print the public URL or error.
"""
import os
from dotenv import load_dotenv
from supabase import create_client
import time

load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
BUCKET = os.getenv('SUPABASE_CERT_BUCKET', 'training_certificates')

if not SUPABASE_URL or not SUPABASE_KEY:
    print('Missing SUPABASE_URL or SUPABASE_KEY in environment (.env)')
    raise SystemExit(1)

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Check if bucket exists
try:
    buckets = supabase.storage.list_buckets()
    print('Available buckets:', [b.name for b in buckets])
    if not any(b.name == BUCKET for b in buckets):
        print(f'Bucket "{BUCKET}" does not exist. Creating it...')
        supabase.storage.create_bucket(BUCKET, {'public': True})
        print(f'Bucket "{BUCKET}" created.')
    else:
        print(f'Bucket "{BUCKET}" exists.')
except Exception as e:
    print('Error checking buckets:', repr(e))

# Check if training_certificates table exists
try:
    resp = supabase.table("training_certificates").select("*", count="exact").limit(1).execute()
    print('training_certificates table exists, count:', resp.count)
except Exception as e:
    print('training_certificates table does not exist or error:', repr(e))

contents = b'Test upload from local script at ' + str(time.time()).encode('utf-8')
filename = f'test_upload_{int(time.time())}.txt'
path = f'test/{filename}'

print('Uploading to bucket:', BUCKET)
try:
    resp = supabase.storage.from_(BUCKET).upload(path, contents, {'content-type': 'text/plain'})
    print('Upload response:', resp)
    public = supabase.storage.from_(BUCKET).get_public_url(path)
    print('Public URL:', public)
except Exception as e:
    print('Upload failed:', repr(e))
    raise
