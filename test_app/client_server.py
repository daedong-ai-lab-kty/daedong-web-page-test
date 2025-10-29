from flask import Flask, render_template

app = Flask(__name__)

# 'About' 페이지
@app.route('/')
def about():
    return render_template('index.html')

@app.route('/diaries')
def diaries():
    return render_template('diaries.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8559)
    

