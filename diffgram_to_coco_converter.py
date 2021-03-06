import json
from diffgram import Project
import csv
import urllib.request
import pathlib
import cv2
import requests

current_path = pathlib.Path().absolute()

# Replace with your Diffgram Project.
client_id = "you client ID"
client_secret = "your client secret"
project = Project(
    project_string_id = "project string ID",
    client_id = client_id,
    client_secret = client_secret)

# Change this to your bucket name in GCP.
GCP_BUCKET_NAME = 'video-footage-07'

def get_frame_from_diffgram(frame_number, project_string_id, parent_file_id):
    url  = 'https://diffgram.com/api/project/{}/video/single/{}/frame/{}'.format(
        project_string_id,
        parent_file_id,
        frame_number
    )
    res = requests.get(url, params = None, auth= (client_id, client_secret))
    url = res.json()['url']
    img_path = '{}/images/{}.jpg'.format(current_path, frame_number)
    urllib.request.urlretrieve(url, img_path)
    print(url)
    return url

def convert_goombas_to_coco(diffgram_export_file_path, output_path = '.'):
    """
        Converts the given Diffgram JSON file into COCO file and outputs them into the output
        path provided.
    :param diffgram_export_file_path: The path to the JSON file generated by Diffgram
    :param output_path: The Ouput path where the CSV files are going to be placed.
    :return:
    """
    # Let's get the file from the given path
    file = open(diffgram_export_file_path)
    # Now transform it into a python dict.
    export_file_data = json.load(file)
    # Let's pop some keys of the dict to keep only the file IDs
    coco_dict = {
        "info": {
            "description": "Goombas Dataaset Test",
            "url": "https://github.com/diffgram/goomba-detector",
            "version": "1.0",
            "year": 2020,
            "contributor": "Pablo Estrada",
            "date_created": "2020/10/25",
        },
        "licenses": {
            "url": "https://creativecommons.org/licenses/by/4.0/",
            "id": 1,
            "name": "Attribution License"
        },
        "categories": [
            {
                "id": 1,
                "name": "goomba",
                "supercategory": "enemy"
            }
        ],
        "images": [],
        "annotations": []
    }
    label_map = export_file_data.pop('label_map')
    export_file_data.pop('export_info')
    export_file_data.pop('attribute_groups_reference')
    frames = {}

    num_files = export_file_data.items()
    i = 0
    for file_id, file_data in export_file_data.items():
        file_data = export_file_data[file_id]
        file = project.file.get_by_id(id = int(file_id))
        path_save_video = '{}/goombas_{}.mp4'.format(current_path, file_id)
        urllib.request.urlretrieve(file.video['file_signed_url'], path_save_video)
        vcap = cv2.VideoCapture(path_save_video)  # 0=camera
        if vcap.isOpened():
            width = vcap.get(3)
            height = vcap.get(4)
            print(width, height)
        for sequence in file_data['sequence_list']:
            sequence_id = sequence['id']
            j = 0
            instance_list = sequence['instance_list']

            for instance in instance_list:

                global_frame_number = instance['global_frame_number']
                frame_number = instance['frame_number']
                if not frames.get(global_frame_number):
                    image_coco = {
                        "id": global_frame_number,
                        "license": 1,
                        "coco_url": get_frame_from_diffgram(global_frame_number, 'goomba-detector', file_id),
                        "file_name": "{}.jpg".format(global_frame_number),
                        "width": width,
                        "height": height,
                        "date_captured": "2020-11-15 02:41:42"
                    }
                    frames[global_frame_number] = image_coco
                    coco_dict['images'].append(image_coco)
                x_min = instance['x_min']
                x_max = instance['x_max']
                y_min = instance['y_min']
                y_max = instance['y_max']
                width_instance = x_max - x_min
                height_instance = y_max - y_min
                coco_instance = {
                    "id": sequence_id + j,
                    "category_id": 1,
                    "iscrowd": 0,
                    "image_id": global_frame_number,
                    "bbox": [x_min, y_min, width_instance, height_instance]
                }
                coco_dict['annotations'].append(coco_instance)
                j += 1
        i += 1

    print('INSTANCEEES', len(coco_dict['annotations']))
    coco_dict_val = coco_dict.copy()
    count = 0
    for image in coco_dict_val['images']:
        if count == 200:
            pass

    with open('goombas_training_coco.json', 'w') as fp:
        json.dump(coco_dict, fp)


import os.path
def download_images_coco_file(coco_path):
    """
        Get all images in coco json file and download them into a folder.
    :param coco_path: Path to coco file
    :return:
    """
    # Let's get the file from the given path
    file = open(coco_path)
    # Now transform it into a python dict.
    coco_data = json.load(file)
    count = 0
    new_images = []
    print(coco_data['images'])
    for image in coco_data['images']:
        try:
            if count > 189:
                print(image['id'])
            img_path = '{}/images/{}.jpg'.format(current_path, image['id'])
            if os.path.isfile(img_path):
                new_images.append(image)
        except Exception as e:
            raise e
        count += 1
    print(count)

def build_images_from_instances(coco_path):
    file = open(coco_path)
    # Now transform it into a python dict.
    coco_data = json.load(file)
    count = 0
    new_images = []
    ids = []
    for ann in coco_data['annotations']:
        img_path = '{}/images/{}.jpg'.format(current_path, ann['image_id'])
        if os.path.isfile(img_path) and ann['image_id'] not in ids:
            ids.append(ann['image_id'])
            new_images.append({
                'id': ann['image_id'],
                'name': '{}.jpg'.format(ann['image_id']),
                "license": 1,
                'width': 640,
                'height': 360
            })

    print(new_images)
    coco_data['images'] = new_images
    with open('goombas_training_coco.json', 'w') as fp:
        json.dump(coco_data, fp)