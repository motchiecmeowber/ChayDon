# Chạy Đơn

Game mobile màn hình dọc, Nhóm 5, môn Lập trình Game CO3045. Người chơi là shipper chạy xe máy giao hàng qua phố và hẻm Quận 1.

## Mở dự án

1. Cài **Unity 6000.3.28f1** (Unity 6.3 LTS) qua Unity Hub, có module **Android Build Support**.
2. Cài **Git LFS** rồi clone:
   ```
   git lfs install
   git clone <link repo>
   ```
3. Unity Hub → **Add project from disk** → chọn thư mục vừa clone. Lần mở đầu Unity sẽ tạo lại `Library/`, mất vài phút.

## Import hai gói Asset Store (bắt buộc)

Hai gói này không nằm trong repo vì giấy phép Standard Unity Asset Store EULA không cho phát tán file gốc. Mỗi người tự lấy (miễn phí):

| Gói | Tác giả | Link |
|---|---|---|
| Low Poly Cars | Broken Vector | https://assetstore.unity.com/packages/3d/vehicles/land/low-poly-cars-101798 |
| Pho Dining Set: Free Low Poly Asian Street Food | AlleyBits | https://assetstore.unity.com/packages/3d/environments/urban/pho-dining-set-free-low-poly-asian-street-food-410814 |

1. Mở link, bấm **Add to My Assets**.
2. Trong Unity: **Window → Package Manager → My Assets** → chọn gói → **Download** → **Import** → bấm **Import** trong cửa sổ hiện ra.
3. Sau khi import Low Poly Cars, chạy menu **Chạy Đơn → Chuyển vật liệu Low Poly Cars sang URP** để xe không bị hồng.

## Cấu trúc

| Thư mục | Nội dung |
|---|---|
| `Assets/_Project/Art/Models` | Model low-poly tự tạo: `Pho`, `Duong`, `Hem`, `CongVien`, `Nguoi`, `HangHoa`, `XeShipper`, `XeAI` |
| `Assets/_Project/Art/Textures` | `BangMau_LowPoly.png`: ảnh bảng màu dùng chung cho mọi model tự tạo |
| `Assets/_Project/Art/Greybox` | Đường và vật cản dạng khối thô, dùng thử nghiệm |
| `Assets/_Project/Scripts` | Code game; `Scripts/Editor` là công cụ trong Editor |
| `Tools/Blender` | Script Python sinh toàn bộ model low-poly và ảnh xem trước (`XemTruoc/`) |

## Sinh lại model bằng Blender

Cần Blender 5.2. Chạy trong thư mục `Tools/Blender`:

```
blender --background --factory-startup --python tao_asset_lowpoly.py -- ../../Assets/_Project/Art
```

Thêm tên nhóm ở cuối để chỉ dựng một phần: `cu`, `cong_trinh`, `cong_trinh2`, `cong_vien`, `hem`, `hem2`, `duong`, `nga_re`, `vat_can`, `xe_ai`, `xe_dong`, `dia_diem`, `nha_o`. Mỗi lần chạy đều sinh lại hai ảnh bảng màu `BangMau_LowPoly.png` và `BangMau_Quan3.png`. Model sinh ra ghi đè file cũ nhưng giữ nguyên file `.meta`, nên liên kết trong scene không bị mất.

Quy ước: 1 đơn vị = 1 m; gốc model ở giữa đáy; mặt trước model quay về **+Z** trong Unity; đường kéo dài theo +Z.

Các model trong `Assets/_Project/Art` được tạo bằng script Python chạy trong Blender; script được viết với sự hỗ trợ của AI (Claude, Anthropic).
