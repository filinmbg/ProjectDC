from sqlalchemy.ext.asyncio import AsyncSession
from src.entity.models import Vehicle, MovementLog
import cloudinary.uploader
import os
import requests
import matplotlib.pyplot as plt
import numpy as np
import cv2
from tensorflow.keras.models import load_model
from src.conf.config import config
from sqlalchemy import select

from src.repository.payments import calculate_parking_cost

# Визначення шляхів для завантаження ресурсів
models_file_path = 'src/models'
file_model = 'ua-license-plate-recognition-model-37x.h5'
file_cascad = 'haarcascade_russian_plate_number.xml'
full_path_models = os.path.join(models_file_path, file_model)
full_path_cascad = os.path.join(models_file_path, file_cascad)

# Завантаження моделі та каскадного класифікатора
model = load_model(full_path_models)
plate_cascade = cv2.CascadeClassifier(full_path_cascad)


async def create_vehicle(db: AsyncSession, vehicle_data: dict):
    vehicle = Vehicle(**vehicle_data)
    async with db() as session:
        session.add(vehicle)
        await session.commit()
        await session.refresh(vehicle)
        return vehicle


def upload_to_cloudinary(image):
    return cloudinary.uploader.upload(image, folder="vehicles")


# зменшення зображення по висоті 720
def resize_img(img, target_height=720):
    # Отримання висоти та ширини вихідного зображення
    height, width = img.shape[:2]
    if height <= target_height:
        return img
    # Розрахунок пропорційної ширини
    target_width = int(width * (target_height / height))
    # Зменшення розміру зображення до нових розмірів
    resized_img = cv2.resize(img, (target_width, target_height))
    return resized_img


# Визначає та виконує розмиття на номерних знаках
def extract_plate(img, plate_cascade, text=''):
    # Завантажує дані, необхідні для виявлення номерних знаків, з каскадного класифікатора.
    # plate_cascade = cv2.CascadeClassifier(full_path_cascad)
    # plate_cascade = cv2.CascadeClassifier('D:\Python\github\PlateN\DS\models\haarcascade_russian_plate_number.xml')

    plate_img = img.copy()
    roi = img.copy()
    plate = None
    # Виявляє номерні знаки та повертає координати та розміри контурів виявлених номерних знаків.
    plate_rect = plate_cascade.detectMultiScale(plate_img, scaleFactor=1.05, minNeighbors=8)

    width_max = 0  # використовується для сортування за шириною
    plate_max = None
    x_max = 0
    y_max = 0

    for (x, y, w, h) in plate_rect:

        # виконує пропорційне зміщення пікселів
        a, b = (int(0.1 * h), int(0.1 * w))
        aa, bb = (int(0.1 * h), int(0.1 * w))

        if h > 75:  # пропускає розбиття за шириною високоякісного зображення
            b = 0
            bb = 0

        plate = roi[y + a: y + h - aa, x + b: x + w - bb, :]

        if width_max < w:
            plate_max = plate
            width_max = w
            x_max = x
            y_max = y

        # представлення виявлених контурів за допомогою малювання прямокутників навколо країв:
        cv2.rectangle(plate_img, (x + 2, y), (x + w - 3, y + h - 5), (51, 224, 172), 3)
    if text != '':
        h = plate_max.shape[0]
        plate_img = cv2.putText(plate_img, text, (x_max, y_max - h // 3),
                                cv2.FONT_HERSHEY_COMPLEX_SMALL, 1.5, (51, 224, 172), 2, cv2.LINE_AA)

    return plate_img, plate_max


# Відповідність контурів номерному або символьному шаблону
def find_contours(dimensions, img):
    i_width_threshold = 6

    # Знайдіть всі контури на зображенні
    cntrs, _ = cv2.findContours(img.copy(), cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    # Отримайте потенційні розміри
    lower_width = dimensions[0]
    upper_width = dimensions[1]
    lower_height = dimensions[2]
    upper_height = dimensions[3]

    # Перевірте найбільші 16 контурів на номерний або символьний шаблон
    cntrs = sorted(cntrs, key=cv2.contourArea, reverse=True)[:16]

    # бінарне зображення номерного знака на вхід: щоб перетворити img.shape(h,w) на img.shape(h,w,3)
    ii = np.dstack([img] * 3)

    x_cntr_list = []
    target_contours = []
    img_res = []
    for cntr in cntrs:
        # виявлення контуру на бінарному зображенні і повернення координат прямокутника, який його оточує
        X, Y, W, H = cv2.boundingRect(cntr)

        # перевірка розмірів контуру для фільтрації символів за розміром контуру
        if (
                W >= i_width_threshold and W < upper_width and H > lower_height and H < upper_height):
            x_cntr_list.append(
                X)  # stores the x coordinate of the character's contour, to used later for indexing the contours

            char_copy = np.zeros((44, 24))
            # видобуття кожного символу, використовуючи координати прямокутника, що його оточує.
            char = img[Y:Y + H, X:X + W]

            if (W >= i_width_threshold and W < lower_width):
                i_char = cv2.resize(char, (W, 42), interpolation=cv2.INTER_LINEAR_EXACT)

                char = np.full((42, 22), 255, dtype=np.uint8)
                begin = int((22 - W) / 2)  # center alignment
                char[:, begin:begin + W] = i_char[:, :]
            else:
                char = cv2.resize(char, (22, 42), interpolation=cv2.INTER_LINEAR_EXACT)

            cv2.rectangle(ii, (X, Y), (W + X, Y + H), (50, 21, 200), 2)
            plt.imshow(ii, cmap='gray')

            # Make result formatted for classification: invert colors
            char = cv2.subtract(255, char)

            # Resize the image to 24x44 with black border
            char_copy[1:43, 1:23] = char
            char_copy[0:1, :] = 0
            char_copy[:, 0:1] = 0
            char_copy[43:44, :] = 0
            char_copy[:, 23:24] = 0

            img_res.append(char_copy)  # List that stores the character's binary image (unsorted)
            if len(img_res) >= 10: break

    # Return characters on ascending order with respect to the x-coordinate (most-left character first)

    # arbitrary function that stores sorted list of character indeces
    indices = sorted(range(len(x_cntr_list)), key=lambda k: x_cntr_list[k])
    img_res_copy = []
    for idx in indices:
        img_res_copy.append(img_res[idx])  # stores character images according to their index
    img_res = np.array(img_res_copy)

    return img_res


# Find characters in the resulting images
def segment_to_contours(image):
    new_height = 75  # set fixed height
    # Preprocess cropped license plate image
    img_lp = cv2.resize(image, (333, new_height), interpolation=cv2.INTER_LINEAR_EXACT)

    img_gray_lp = cv2.cvtColor(img_lp, cv2.COLOR_BGR2GRAY)
    _, img_binary_lp = cv2.threshold(img_gray_lp, 112, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    LP_WIDTH = img_binary_lp.shape[1]
    LP_HEIGHT = img_binary_lp.shape[0]

    # Make borders white
    img_binary_lp[0:3, :] = 255
    img_binary_lp[:, 0:3] = 255
    img_binary_lp[new_height - 3:new_height, :] = 255
    img_binary_lp[:, 330:333] = 255

    # Estimations of character contours sizes of cropped license plates
    dimensions = [LP_WIDTH / 24,
                  LP_WIDTH / 8,
                  LP_HEIGHT / 3,
                  2 * LP_HEIGHT / 3]

    # Get contours within cropped license plate
    char_list = find_contours(dimensions, img_binary_lp)
    return char_list


def fix_dimension(img):
    new_img = np.zeros((28, 28, 3))
    for i in range(3):
        new_img[:, :, i] = img
    return new_img


# Predicting the output string number by contours
def predict_result(ch_contours, model):
    dic = {}
    characters = '#0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    for i, c in enumerate(characters):
        dic[i] = c
    output = []
    for i, ch in enumerate(ch_contours):
        img_ = cv2.resize(ch, (28, 28))  # interpolation=cv2.INTER_LINEAR by default
        img = fix_dimension(img_)
        img = img.reshape(1, 28, 28, 3)  # preparing image for the model
        y_ = np.argmax(model.predict(img, verbose=0), axis=-1)[0]  # predicting the class
        character = dic[y_]
        output.append(character)
    plate_number = ''.join(output)
    return plate_number


def get_num_avto(img_avto):
    img = img_avto.copy()
    output_img, num_img = extract_plate(img, plate_cascade)
    chars = segment_to_contours(num_img)
    predicted_str = predict_result(chars, model)
    num_avto_str = str.replace(predicted_str, '#', '')
    return num_avto_str, num_img


################################################################################
async def get_car_info_by_license_plate(license_plate):
    # URL сервісу, який повертає інформацію по номерному знаку
    key = config.BGCARS_API_KEY
    url = f"https://baza-gai.com.ua/nomer/{license_plate}"
    try:
        # Виконуємо GET-запит до сервера
        response = requests.get(url, headers={"Accept": "application/json", "X-Api-Key": key})
        # Перевіряємо, чи отримали ми успішну відповідь
        if response.status_code == 200:
            data = response.json()
            car_info_by_license_plate = {
                'plate': license_plate,
                'brand': data["vendor"],
                'model': data["model"],
                'year': data["model_year"],
                'color': data["operations"][0]["color"]["ua"],
                'body': data["operations"][0]["kind"]["ua"]
            }
            return car_info_by_license_plate
        else:
            # Якщо відповідь не успішна, викидаємо помилку
            raise Exception(f"Request failed with status code {response.status_code}")
    except Exception as e:
        # Обробляємо будь-які помилки, які можуть виникнути при виконанні запиту
        print(f"Error occurred: {e}")
        return None


async def car_info_response(url):
    # Завантаження зображення за URL
    response = requests.get(url)

    # Перевірка статусу відповіді
    if response.status_code == 200:
        # Читання зображення з буфера пам'яті
        nparr = np.frombuffer(response.content, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        # Перевірка, чи було прочитано зображення
        if img is not None:
            result = get_num_avto(img)
            if result:
                car_info = await get_car_info_by_license_plate(result[0])
                if car_info:
                    return car_info
                else:
                    return None
            else:
                return None
        else:
            return None
    else:
        return response.status_code


async def get_vehicle_info_by_plate(plate: str, session: AsyncSession) -> dict:
    # Отримати інформацію про автомобіль за номерним знаком
    vehicle_result = await session.execute(select(Vehicle).filter(Vehicle.plate == plate))
    vehicle = vehicle_result.scalars().first()
    if not vehicle:
        return {"error": "Vehicle not found"}

    # Отримати історію паркувань автомобіля
    movement_logs_result = await session.execute(select(MovementLog).filter(MovementLog.vehicle_id == vehicle.id))
    movement_logs = movement_logs_result.scalars().all()


    # Створимо об'єкт Pydantic для інформації про автомобіль
    vehicle_info = {
        "id": vehicle.id,
        "plate": vehicle.plate,
        "brand": vehicle.brand,
        "model": vehicle.model,
        "year": vehicle.year,
        "color": vehicle.color,
        "body": vehicle.body,
        "plate_photo": vehicle.plate_photo,
        "is_blocked": vehicle.is_blocked
    }

    # Створимо список об'єктів Pydantic для історії паркувань
    movement_logs_info = []
    for movement_log in movement_logs:
        movement_log_info = {
            "id": movement_log.id,
            "user_id": movement_log.user_id,
            "vehicle_id": movement_log.vehicle_id,
            "entry_time": movement_log.entry_time,
            "exit_time": movement_log.exit_time,
            "parking_spot_id": movement_log.parking_spot_id,
            "status": movement_log.status
        }
        movement_logs_info.append(movement_log_info)

    payment = await calculate_parking_cost(session, movement_logs[-1].id)
    print(payment)

    return {
        "vehicle_info": vehicle_info,
        "movement_logs": movement_logs_info,
        "payment": payment,
    }