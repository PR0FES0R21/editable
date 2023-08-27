from flask import Flask, request, render_template, jsonify, Response, redirect, url_for, send_file
from pymongo import MongoClient
import os
from io import StringIO
import html
import shutil
import zipfile

client = MongoClient('mongodb+srv://root:root@cluster0.owno83m.mongodb.net/?retryWrites=true&w=majority')
db = client.dbjoki


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/tambahUser')
def tambahUser():
    return render_template('tambah_user.html')

@app.route('/tambah_user', methods=['POST'])
def addUser():
    username = html.escape(request.form.get('username'))
    mongodb_url = html.escape(request.form.get('mongodb-url'))
    dbname = html.escape(request.form.get('dbname'))

    doc = {
        'username': username,
        'mongodbUrl': mongodb_url,
        'dbname': dbname
    }

    db.user.insert_one(doc)

    return redirect(url_for('tambahUser'))


@app.route('/add_file')
def add_file():
    return render_template('add_tugas.html')


@app.route('/save_file', methods=['POST'])
def save_file():
    file = request.files['file-tugas']
    tugasName = request.form.get('nama-tugas')
    keterangan = request.form.get('keterangan')

    filename = file.filename

    file.save(f'zipfile/{filename}')

    db.file_tugas.insert_one({
        'fileName': filename.split(".")[0],
        'tugasName': tugasName,
        'keterangan': keterangan
    })

    ekstrak_file(filename)

    return redirect(url_for('add_file'))


# globals
@app.route('/getData', methods=['GET'])
def getUser():

    collection_name = request.args.get('collection')

    collection = db[collection_name]

    data = collection.find({}, {'_id': False})

    user_list = list(data)

    return user_list

@app.route('/directory')
def directory():
    base_path = 'file'
    file_path = 'final_file'
    
    folder_names = [folder for folder in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, folder))]

    file_list = [file for file in os.listdir(file_path) if os.path.isfile(os.path.join(file_path, file))]
    
    return render_template('directory.html', folder_names=folder_names, file_list=file_list)

@app.route('/delete_folder', methods=['POST'])
def delete_folder():
    foldername = request.form.get('folderName')

    shutil.rmtree(f'file/{foldername}')

    db.file_tugas.delete_one({'fileName': foldername})


    return jsonify({'msg': f'Folder {foldername} Berhasil Dihapus!'})


@app.route('/delete_file', methods=['POST'])
def delete_file():
    file_path = request.form.get('filename')

    try:
        os.remove(f'final_file/{file_path}')  # Menghapus file menggunakan os.remove()
        return jsonify({'msg': f'File {file_path} Berhasil Dihapus!'})
    except Exception as e:
        return jsonify({'msg': str(e)})



def getdataByName(username):
    data = db.user.find_one({'username': username}, {'_id': False})
    return data

def ekstrak_file(filename):

    # Path arsip yang ingin diekstrak
    path_arsip = f'zipfile/{filename}'

    # Path tujuan ekstraksi
    path_ekstraksi = f'file/{filename.split(".")[0]}'
    
    # Ekstrak arsip
    shutil.unpack_archive(path_arsip, path_ekstraksi)

    os.remove(f'zipfile/{filename}')

@app.route('/download', methods=['POST'])
def modify_and_download():

    
    username = request.form.get('user')
    filename = request.form.get('tugas')

    proses_file_tugas(username, filename)

    p = f'final_file/{filename}_{username}.zip'

    return jsonify({
        'msg': 'download akan dimulai',
        'filename': filename,
        'username': username
    })

def proses_file_tugas(username, filename):

    source_directory = f'file/{filename}'
    destination_directory = f'file_proses/{filename}'

    user_data = getdataByName(username)

    print(user_data)


    mongoDbUrl = user_data.get("mongodbUrl")
    dbname = user_data.get("dbname")


    shutil.copytree(source_directory, destination_directory)

    file_path = f'file_proses/{filename}/app.py'

    # Buka file dalam mode baca ('r')
    with open(file_path, 'r') as file:
        content = file.read()

    # Lakukan pengeditan pada konten file
    new_content = content.replace('$', mongoDbUrl).replace('dbname', dbname)

    # Buka file dalam mode tulis ('w') untuk menyimpan konten yang sudah diubah
    with open(file_path, 'w') as file:
        file.write(new_content)

    # Mengarsipkan folder 'file/minggu' menjadi file zip setelah dimodifikasi
    shutil.make_archive(f'final_file/{filename}_{username}', 'zip', 'file_proses', filename)

    folder_path = f'file_proses/{filename}'
    shutil.rmtree(folder_path)


@app.route('/downloads')
def downloads():

    username = request.args.get('username')
    filename = request.args.get('filename')

    p = f'final_file/{filename}_{username}.zip'

    return send_file(p, as_attachment=True, mimetype='application/zip')


@app.route('/download_manual')
def download_manual():

    filename = request.args.get('filename')

    p = f'final_file/{filename}'

    return send_file(p, as_attachment=True, mimetype='application/zip')

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)
