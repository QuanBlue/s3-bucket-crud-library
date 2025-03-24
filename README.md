python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

export AWS_REQUEST_CHECKSUM_CALCULATION=when_required
export AWS_RESPONSE_CHECKSUM_VALIDATION=when_required

python3 main.py