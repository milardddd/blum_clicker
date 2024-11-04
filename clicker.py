import cv2
import numpy as np
import pyautogui
import pygetwindow as gw
import keyboard as keyb

def capture_screen(window_title):
    try:
        target_window = gw.getWindowsWithTitle(window_title)[0]
        screenshot = pyautogui.screenshot(region=(target_window.left, target_window.top,
                                                   target_window.width, target_window.height))
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        offset_x = target_window.left
        offset_y = target_window.top
        return screenshot, offset_x, offset_y
    except IndexError:
        print(f"Окно с заголовком '{window_title}' не найдено.")
        return None, 0, 0

def detect_targets(image, lower_color, upper_color):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_image, lower_color, upper_color)
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def detect_bombs(image, lower_color, upper_color):
    hsv_image = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv_image, lower_color, upper_color)
    contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    return contours

def detect_button(image, button_template):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    res = cv2.matchTemplate(gray_image, button_template, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
    return max_val, max_loc

def click_targets(target_contours, bomb_contours, offset_x, offset_y):
    clicked_points = []
    for target in target_contours:
        if cv2.contourArea(target) > 50:
            target_points = [point[0] for point in target]
            should_click = True
            
            for bomb in bomb_contours:
                if cv2.contourArea(bomb) > 50 and is_within(target, bomb):
                    should_click = False
                    break

            if should_click:
                M = cv2.moments(target)
                if M['m00'] != 0:
                    cx = int(M['m10'] / M['m00'])
                    cy = int(M['m01'] / M['m00'])
                    click_x = cx + offset_x
                    click_y = cy + offset_y
                    if (click_x, click_y) not in clicked_points:
                        clicked_points.append((click_x, click_y))
                        try:
                            pyautogui.click(click_x, click_y, interval=0.001)
                        except Exception as e:
                            print(f"{get_message_prefix()}Ошибка при клике: {e}")
                        pyautogui.PAUSE = 0

def is_within(contour1, contour2):
    for point in contour1:
        pt = (int(point[0][0]), int(point[0][1]))  # Убедитесь, что точки имеют правильный формат
        if cv2.pointPolygonTest(contour2, pt, False) >= 0:
            return True
    return False

def get_message_prefix():
    return "<https://t.me/BlumGPT1> "

def main():
    target_window_title = "Telegram"
    
    # Определяем диапазон для зеленого цвета в HSV
    target_lower_color = np.array([35, 100, 100])
    target_upper_color = np.array([85, 255, 255])
    
    # Определяем диапазон для серого цвета в HSV
    bomb_lower_color = np.array([0, 0, 50])
    bomb_upper_color = np.array([180, 50, 200])

    play_button_image_path = "media/lobby-play.png"
    continue_button_image_path = "media/continue-play.png"
    
    play_button_template = cv2.imread(play_button_image_path, cv2.IMREAD_GRAYSCALE)
    continue_button_template = cv2.imread(continue_button_image_path, cv2.IMREAD_GRAYSCALE)
    
    if play_button_template is None:
        print(f"{get_message_prefix()}Не удалось загрузить изображение кнопки Play из {play_button_image_path}")
        return

    if continue_button_template is None:
        print(f"{get_message_prefix()}Не удалось загрузить изображение кнопки Continue из {continue_button_image_path}")
        return

    print(f"{get_message_prefix()}Нажмите '1', чтобы начать, и '2', чтобы остановить")

    running = False
    status_printed = False

    while True:
        if keyb.is_pressed('1') and not running:
            print(f"{get_message_prefix()}Нажата клавиша '1'. Запуск скрипта...")
            running = True
            status_printed = False  # Сброс флага при запуске

        if keyb.is_pressed('2') and running:
            print(f"{get_message_prefix()}Нажата клавиша '2'. Остановка скрипта.")
            running = False

        if running:
            image, offset_x, offset_y = capture_screen(target_window_title)
            if image is None:
                print(f"{get_message_prefix()}Не удалось захватить изображение.")
                continue

            # Проверяем наличие кнопки Play
            max_val, max_loc = detect_button(image, play_button_template)
            threshold = 0.8
            if max_val >= threshold:
                button_x = max_loc[0] + offset_x
                button_y = max_loc[1] + offset_y
                button_center_x = button_x + play_button_template.shape[1] // 2
                button_center_y = button_y + play_button_template.shape[0] // 2
                pyautogui.click(button_center_x, button_center_y, interval=0.001)
                print(f"{get_message_prefix()}Кнопка Play была нажата.")
                continue  # Пропускаем основной код, если кнопка была найдена и нажата

            # Проверяем наличие кнопки Continue
            max_val, max_loc = detect_button(image, continue_button_template)
            if max_val >= threshold:
                button_x = max_loc[0] + offset_x
                button_y = max_loc[1] + offset_y
                button_center_x = button_x + continue_button_template.shape[1] // 2
                button_center_y = button_y + continue_button_template.shape[0] // 2
                pyautogui.click(button_center_x, button_center_y, interval=0.001)
                print(f"{get_message_prefix()}Код работает...")
                continue  # Пропускаем основной код, если кнопка была найдена и нажата

            # Обнаруживаем мишени и бомбочки
            target_contours = detect_targets(image, target_lower_color, target_upper_color)
            bomb_contours = detect_bombs(image, bomb_lower_color, bomb_upper_color)
            
            if not status_printed:
                print(f"{get_message_prefix()}Код работает...")
                status_printed = True

            click_targets(target_contours, bomb_contours, offset_x, offset_y)

if __name__ == "__main__":
    main()
