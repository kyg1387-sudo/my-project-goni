@echo off
REM yanagi-final.mp4 merge (Windows). Put this file in the same folder as the 16 part files and double-click.
cd /d "%~dp0"
copy /b yanagi-final.mp4.part-00+yanagi-final.mp4.part-01+yanagi-final.mp4.part-02+yanagi-final.mp4.part-03+yanagi-final.mp4.part-04+yanagi-final.mp4.part-05+yanagi-final.mp4.part-06+yanagi-final.mp4.part-07+yanagi-final.mp4.part-08+yanagi-final.mp4.part-09+yanagi-final.mp4.part-10+yanagi-final.mp4.part-11+yanagi-final.mp4.part-12+yanagi-final.mp4.part-13+yanagi-final.mp4.part-14+yanagi-final.mp4.part-15 yanagi-final.mp4
if exist yanagi-final.mp4 (echo OK: yanagi-final.mp4 created) else (echo FAILED: check that all 16 part files are here)
pause
