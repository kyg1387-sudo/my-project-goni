@echo off
cd /d %~dp0
if exist blackcard-final.mp4 del blackcard-final.mp4
copy /b blackcard-final.mp4.part-00+blackcard-final.mp4.part-01+blackcard-final.mp4.part-02+blackcard-final.mp4.part-03+blackcard-final.mp4.part-04+blackcard-final.mp4.part-05+blackcard-final.mp4.part-06+blackcard-final.mp4.part-07+blackcard-final.mp4.part-08+blackcard-final.mp4.part-09+blackcard-final.mp4.part-10+blackcard-final.mp4.part-11+blackcard-final.mp4.part-12+blackcard-final.mp4.part-13+blackcard-final.mp4.part-14+blackcard-final.mp4.part-15 blackcard-final.mp4
if errorlevel 1 echo JOIN FAILED - check that all 16 part files are in this folder
dir blackcard-final.mp4
echo DONE: blackcard-final.mp4 (expected 465,439,006 bytes)
pause
