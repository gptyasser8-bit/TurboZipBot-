FROM python:3.9

WORKDIR /code

# تثبيت المتطلبات
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

COPY . .

# فتح المنفذ الذي يطلبه Render عادةً أو الذي حددته أنت
EXPOSE 7860

# تأكد أن اسم الملف هنا هو نفس اسم ملف الكود (main.py)
CMD ["python", "main.py"]
