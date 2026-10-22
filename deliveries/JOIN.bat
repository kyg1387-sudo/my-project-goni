@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 17개 조각을 합치는 중...
copy /b "ryokan-complete.mp4.part-00"+"ryokan-complete.mp4.part-01"+"ryokan-complete.mp4.part-02"+"ryokan-complete.mp4.part-03"+"ryokan-complete.mp4.part-04"+"ryokan-complete.mp4.part-05"+"ryokan-complete.mp4.part-06"+"ryokan-complete.mp4.part-07"+"ryokan-complete.mp4.part-08"+"ryokan-complete.mp4.part-09"+"ryokan-complete.mp4.part-10"+"ryokan-complete.mp4.part-11"+"ryokan-complete.mp4.part-12"+"ryokan-complete.mp4.part-13"+"ryokan-complete.mp4.part-14"+"ryokan-complete.mp4.part-15"+"ryokan-complete.mp4.part-16" "ryokan-complete.mp4"
if errorlevel 1 (echo 실패: 조각 17개가 같은 폴더에 있는지 확인하세요 & pause & exit /b 1)
echo.
echo 완료: ryokan-complete.mp4 (약 472MB, 10:21)
pause
