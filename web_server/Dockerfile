# Gunakan image Python 3.10
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy semua file project ke dalam container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Pastikan folder static dan subfolder-nya ada
RUN mkdir -p /app/static/videos

# 👇 Tambahkan volume agar folder static bisa diakses dari host (D:\eFishery-cv\web_server\static)
VOLUME ["/app/static"]

# Expose port Flask
EXPOSE 5000

# Jalankan server Flask
CMD ["python", "app.py"]
