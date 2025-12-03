"""Quick test: create a tiny WAV, upload to S3 and update DynamoDB using utilities.

Usage: run from the `backend` folder: `python scripts/test_s3_dynamo.py`
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
        wf.setsampwidth(2)  # 16-bit
        wf.setframerate(rate)
        wf.writeframes(b'\x00\x00' * n_frames)


def main():
    try:
        test_wav = os.path.join(HERE, 'tmp_test.wav')
        make_silence_wav(test_wav)
        print('WAV created:', test_wav)

        from app.utils.s3_utils import upload_audio
        from app.utils.dynamo_utils import update_job_s3

        user_id = os.getenv('TEST_USER_ID', 'test-user')
        job_id = os.getenv('TEST_JOB_ID', 'test-job-123')

        print('Uploading to S3...')
        s3_key, s3_url = upload_audio(test_wav, user_id, job_id)
        print('Uploaded:', s3_key)
        print('URL:', s3_url)

        print('Updating DynamoDB...')
        update_job_s3(job_id, s3_key, s3_url)
        print('DynamoDB update completed')

        # cleanup
        try:
            os.remove(test_wav)
        except Exception:
            pass

    except Exception:
        traceback.print_exc()
        sys.exit(2)


if __name__ == '__main__':
    main()
