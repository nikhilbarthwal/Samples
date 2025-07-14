from flask import Flask, request, jsonify

app = Flask(__name__)

volumeThreshold = 1000.0 * 1000.0
dimensionThreshold = 150.0
massThreshold = 20.0

def check_param(x, tag):
    try:
        n = float(x)
        if n <=0:
            return n, f"ERROR: {tag} is not positive"
        return n, None
    except:
        return 0, f"ERROR: {tag} is not a number"

@app.route("/")
def helloworld():
    return "Hello World!"

@app.route("/package", methods=['POST'])
def package():
    print(request.form)
    width, error_width = check_param(request.form.get('width'), "Width")
    if error_width is not None:
        return error_width
    print(width)

    height, error_height = check_param(request.form.get('height'), "Height")
    if error_height is not None:
        return error_height
    print(height)

    length, error_length = check_param(request.form.get('length'), "Length")
    if error_length is not None:
        return error_length
    print("Length:", length)

    mass, error_mass = check_param(request.form.get('mass'), "Mass")
    if error_mass is not None:
        return error_mass
    print(mass)

    def check(x):
        return x >= dimensionThreshold

    print(width, height, length)
    volume = width * height * length


    bulky = check(width) or check(height) or check(length) or (volume >= volumeThreshold)
    heavy = (mass >= massThreshold)

    if bulky and heavy:
        return "REJECTED"
    if bulky or heavy:
        return "SPECIAL"
    return "STANDARD"

if __name__ == "__main__":
    app.run()

