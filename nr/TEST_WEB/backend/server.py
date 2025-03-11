from flask import Flask, jsonify
import pandas as pd

app = Flask(__name__)

# CSV 파일 로드
CSV_PATH = "backend/data/musinsa_fake_data.csv"

@app.route("/get-data", methods=["GET"])
def get_data():
    try:
        df = pd.read_csv(CSV_PATH)
        data = df.to_dict(orient="records")  # JSON 형식으로 변환
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
