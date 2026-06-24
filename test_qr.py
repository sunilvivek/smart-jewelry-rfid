import qrcode

img = qrcode.make("RFID100")

img.save("static/qrcodes/RFID100.png")

print("QR created!")