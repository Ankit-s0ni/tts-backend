"""Simulate job completion by creating a dummy WAV, uploading to S3, and updating Dynamo/local DB.
Use when actual Piper model is not available for synthesis.
"""
import os
import sys
import traceback
from dotenv import load_dotenv
import wave

HERE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(HERE, '.env'))

def make_silence_wav(path: str, duration_s: float = 1.0, rate: int = 16000):
    n_frames = int(duration_s * rate)
    with wave.open(path, 'wb') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(rate)
        wf.writeframes(b'\x00\x00' * n_frames)

def main(job_id: str):
    try:
        test_wav = os.path.join(HERE, f'job_{job_id}_dummy.wav')
        make_silence_wav(test_wav)

        from app.utils.s3_utils import upload_audio
        from app.utils.dynamo_utils import update_job_s3
        from app.dynamo import update_job_item

        job = {}  # try to fetch user_id from Dynamo if available
        try:
            from app.dynamo import get_job_item
            job = get_job_item(int(job_id)) or {}
        except Exception:
            pass

        user_id = job.get('user_id') or os.getenv('TEST_USER_ID') or 'e2e-user'

        s3_key, s3_url = upload_audio(test_wav, str(user_id), str(job_id))
        print('Uploaded dummy audio to S3:', s3_key)

        update_job_s3(job_id, s3_key, s3_url)
        print('Updated DynamoDB')

        # update local job record as well
        try:
            update_job_item(job_id, {'status':'completed','audio_s3_key':s3_key,'audio_s3_url':s3_url,'completed_at': __import__('datetime').datetime.utcnow().isoformat()})
        except Exception:
            traceback.print_exc()

        try:
            os.remove(test_wav)
        except Exception:
            pass

    except Exception:
        traceback.print_exc()
        sys.exit(2)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('Usage: python scripts/complete_job_with_dummy_audio.py <job_id>')
        sys.exit(2)
    main(sys.argv[1])
