# COC Farming Bot

Bot Python điều khiển Clash of Clans trên Android emulator bằng ADB. Bot chụp
màn hình, dùng OCR để đọc tài nguyên/trạng thái trận, tìm mục tiêu, thả quân và
có thể nâng cấp tường theo cấu hình tài khoản.

## Công cụ sử dụng

- **Python**: chạy bot và các công cụ hỗ trợ.
- **LDPlayer hoặc Android emulator tương thích ADB**: thiết bị chạy game.
- **Android Debug Bridge (ADB)**: chụp màn hình và gửi thao tác chạm.
- **OpenCV (`opencv-python`) và NumPy**: xử lý ảnh.
- **EasyOCR**: đọc số tài nguyên và trạng thái từ ảnh; mặc định chạy bằng CPU.
- **Git**: quản lý mã nguồn và đẩy dự án lên GitHub/GitLab.

## Cài đặt và cấu hình

1. Cài Python 3.10 hoặc 3.11, Git và LDPlayer (hoặc emulator tương thích).
   Mở game trong emulator và bật/kết nối ADB.
2. Tạo môi trường Python trong thư mục dự án bằng PowerShell:

   ```powershell
   py -3.11 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   python -m pip install --upgrade pip
   python -m pip install numpy opencv-python easyocr
   ```

   Lần đầu chạy EasyOCR có thể cần tải thêm model OCR.
3. Mở `adb.py`, sửa `ADB_PATH` thành đường dẫn `adb.exe` trên máy của bạn.
   Ví dụ hiện tại trong mã đang trỏ tới một đường dẫn LDPlayer cụ thể.
4. Chọn cấu hình trong `accounts/` (ví dụ `accounts/acc1.py`) và cập nhật
   `DEVICE` thành serial ADB của emulator. File account chỉ cần khai báo `NAME`
   và `DEVICE`; các thông số dùng chung được lấy từ `accounts/common.py`, với
   tọa độ nút/OCR trong `accounts/button_common.py`, cấu hình thả quân trong
   `accounts/attack.py` và cấu hình tường trong `accounts/wall.py`. Tọa độ hiện
   thiết lập cho màn hình 1280x720; cần điều chỉnh nếu giao diện hoặc độ phân
   giải khác.

## Chạy bot

Chạy các lệnh từ thư mục dự án, sau khi kích hoạt môi trường ảo:

```powershell
# Chạy chu trình farm và nâng cấp tường
python run_one.py acc1 loop

# Chỉ farm; kiểm tra tài nguyên mỗi 6 trận hoàn thành
python run_one.py acc1 onlyfarm
```

Thay `acc1` bằng tên file cấu hình trong `accounts/` (không kèm `.py`). Có thể
truyền tên một phương thức của `Bot` làm đối số thứ hai để chạy riêng phương
thức đó, ví dụ `python run_one.py acc1 farm_attack`.

### Giao diện Vue: tọa độ và chạy action

Khởi động giao diện cục bộ để chọn tọa độ trên screenshot emulator và chạy các
action của bot ở tiến trình nền:

```powershell
python configure_drop.py acc1
```

Mở `http://127.0.0.1:8765` nếu trình duyệt không tự mở. Giao diện cần ADB đang
kết nối với thiết bị cấu hình. Vue được tải từ unpkg nên trình duyệt cần
internet. Tọa độ có thể chỉnh bằng cách kéo chấm trên ảnh, nhập X/Y hoặc chọn
mục rồi click vị trí tương ứng trên screenshot trong Vue (không mở cửa sổ native
`cv2.selectROI`). Ảnh tự co giãn theo giao diện; X/Y là pixel theo kích thước
ảnh screenshot gốc, không phải pixel hiển thị. Bấm **Lưu JSON** để lưu. Các
giá trị trong `accounts/attack.py` tiếp tục là
config mặc định; giao diện ghi override vào `accounts/acc1.drop.json` và
`run_one.py` áp dụng override này khi bot khởi động. Bấm **Khôi phục config mặc
định** để xóa override. Nếu thay config trong lúc action đang chạy, hãy dừng và
chạy lại action để nó nạp giá trị mới.

Chọn action trong giao diện rồi bấm **Chạy nền**; các action gồm farm, nâng
tường và kiểm tra/thao tác trận hiện có. Log và trạng thái tiến trình hiển thị
tại trang. **Dừng action** kết thúc tiến trình bot hiện tại. Chỉ một action
được chạy tại một thời điểm. Có thể đổi cổng bằng
`python configure_drop.py acc1 --port 8766`.

### Chạy nhiều account

Mỗi account cần một instance LDPlayer đang chạy và một `DEVICE` riêng. Kiểm tra
serial bằng `adb devices` (chỉ dùng dòng có trạng thái `device`), rồi đặt serial
đó trong `accounts/<account>.py`. Ví dụ `acc2.py` chỉ cần import
`accounts.common`, khai báo `NAME = "acc2"` và `DEVICE` của instance thứ hai.

Mở **mỗi lệnh trong một cửa sổ PowerShell riêng**; dùng cổng khác nhau:

```powershell
# PowerShell 1 — account acc1
.\venv\Scripts\python.exe configure_drop.py acc1 --port 8765

# PowerShell 2 — account acc2
.\venv\Scripts\python.exe configure_drop.py acc2 --port 8766
```

Mở `http://127.0.0.1:8765` để điều khiển `acc1` và
`http://127.0.0.1:8766` để điều khiển `acc2`. Không chạy hai account cùng lúc
nếu chúng dùng chung một `DEVICE`. Hiện `accounts/wall.py` lưu trạng thái tường
vào cùng một `wall_state.json`; tránh chạy action `loop` cho nhiều account đồng
thời cho đến khi trạng thái này được tách riêng theo account.

Các tiện ích khác:

- `python main.py [tên_ảnh]`: chụp màn hình emulator `emulator-5554` và lưu vào
  `screenshots/`.
- `pick_point.py`, `select_wall.py` và các script `tools/`: hỗ trợ lấy tọa độ
  và kiểm tra ảnh; xem cấu hình/đường dẫn ở đầu từng script trước khi chạy.
- `recovery.py`: nhận diện màn hình chính LDPlayer qua biểu tượng game trong
  `screenshots/man_hinh_chinh.png`; bot tự mở lại game và thử farm lại nếu bị
  đưa về launcher. Giữ ảnh mẫu này trong dự án để tính năng hoạt động.

## Đẩy dự án lên GitHub

1. Tạo một repository trống trên GitHub (không cần khởi tạo README ở trang web).
2. Trong PowerShell, chuyển đến thư mục dự án rồi chạy:

   ```powershell
   git init
   git add .
   git status
   git commit -m "Initial project"
   git branch -M main
   git remote add origin https://github.com/<username>/<repository>.git
   git push -u origin main
   ```

   Thay `<username>` và `<repository>` bằng thông tin repository của bạn. Nếu
   repository đã có remote `origin`, xem bằng `git remote -v` và dùng
   `git remote set-url origin <URL>` thay vì thêm remote lần nữa.
3. Để đẩy các thay đổi sau này:

   ```powershell
   git add .
   git commit -m "Mô tả thay đổi"
   git push
   ```

Trước khi đẩy, kiểm tra `git status` và nội dung được stage. `.gitignore` loại
trừ môi trường ảo, cache Python và ảnh debug được tạo khi chạy bot. Không commit
mật khẩu, token hoặc thông tin riêng tư; kiểm tra cấu hình trong `accounts/`
trước khi chia sẻ repository. Không nhúng thông tin đăng nhập vào URL Git.