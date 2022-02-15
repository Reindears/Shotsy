import os
import shutil
import time
from pyrogram.types import InputMediaPhoto
import asyncio
from hachoir.metadata import extractMetadata
from hachoir.parser import createParser
import math
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

DEF_WATER_MARK_FILE = ""
DOWNLOAD_LOCATION = "./DOWNLOADS"

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
APP_ID = int(os.environ.get("APP_ID", 12345))
API_HASH = os.environ.get("API_HASH")

Sybot = Client(
    "Screenshot Bot",
    bot_token=os.environ.get("TG_BOT_TOKEN"),
    api_id=int(os.environ.get("APP_ID")),
    api_hash=os.environ.get("API_HASH")
)


async def place_water_mark(input_file, output_file, water_mark_file):
    watermarked_file = output_file + ".watermark.png"
    metadata = extractMetadata(createParser(input_file))
    width = metadata.get("width")
    # https://stackoverflow.com/a/34547184/4723940
    shrink_watermark_file_genertor_command = [
        "ffmpeg",
        "-i", water_mark_file,
        "-y -v quiet",
        "-vf",
        "scale={}*0.5:-1".format(width),
        watermarked_file
    ]
    # print(shrink_watermark_file_genertor_command)
    process = await asyncio.create_subprocess_exec(
        *shrink_watermark_file_genertor_command,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    commands_to_execute = [
        "ffmpeg",
        "-i", input_file,
        "-i", watermarked_file,
        "-filter_complex",
        # https://stackoverflow.com/a/16235519
        # "\"[0:0] scale=400:225 [wm]; [wm][1:0] overlay=305:0 [out]\"",
        # "-map \"[out]\" -b:v 896k -r 20 -an ",
        "\"overlay=(main_w-overlay_w):(main_h-overlay_h)\"",
        # "-vf \"drawtext=text='@FFMovingPictureExpertGroupBOT':x=W-(W/2):y=H-(H/2):fontfile=" + Config.FONT_FILE + ":fontsize=12:fontcolor=white:shadowcolor=black:shadowx=5:shadowy=5\"",
        output_file
    ]
    # print(commands_to_execute)
    process = await asyncio.create_subprocess_exec(
        *commands_to_execute,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    return output_file


async def take_screen_shot(video_file, output_directory, ttl):
    # https://stackoverflow.com/a/13891070/4723940
    out_put_file_name = output_directory + \
        "/" + str(time.time()) + ".jpg"
    file_genertor_command = [
        "ffmpeg",
        "-ss",
        str(ttl),
        "-i",
        video_file,
        "-vframes",
        "1",
        out_put_file_name
    ]
    # width = "90"
    process = await asyncio.create_subprocess_exec(
        *file_genertor_command,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    if os.path.lexists(out_put_file_name):
        return out_put_file_name
    else:
        return None

# https://github.com/Nekmo/telegram-upload/blob/master/telegram_upload/video.py#L26

async def cult_small_video(video_file, output_directory, start_time, end_time):
    # https://stackoverflow.com/a/13891070/4723940
    out_put_file_name = output_directory + \
        "/" + str(round(time.time())) + ".mp4"
    file_genertor_command = [
        "ffmpeg",
        "-i",
        video_file,
        "-ss",
        start_time,
        "-to",
        end_time,
        "-async",
        "1",
        "-strict",
        "-2",
        out_put_file_name
    ]
    process = await asyncio.create_subprocess_exec(
        *file_genertor_command,
        # stdout must a pipe to be accessible as process.stdout
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    # Wait for the subprocess to finish
    stdout, stderr = await process.communicate()
    e_response = stderr.decode().strip()
    t_response = stdout.decode().strip()
    if os.path.lexists(out_put_file_name):
        return out_put_file_name
    else:
        return None


async def generate_screen_shots(
    video_file,
    output_directory,
    is_watermarkable,
    wf,
    min_duration,
    no_of_photos
):
    metadata = extractMetadata(createParser(video_file))
    duration = 0
    if metadata is not None:
        if metadata.has("duration"):
            duration = metadata.get('duration').seconds
    if duration > min_duration:
        images = []
        ttl_step = duration // no_of_photos
        current_ttl = ttl_step
        for looper in range(0, no_of_photos):
            ss_img = await take_screen_shot(video_file, output_directory, current_ttl)
            current_ttl = current_ttl + ttl_step
            if is_watermarkable:
                ss_img = await place_water_mark(ss_img, output_directory + "/" + str(time.time()) + ".jpg", wf)
            images.append(ss_img)
        return images
    else:
        return None

async def progress_for_pyrogram(
    current,
    total,
    ud_type,
    message,
    start
):
    now = time.time()
    diff = now - start
    if round(diff % 10.00) == 0 or current == total:
        # if round(current / total * 100, 0) % 5 == 0:
        percentage = current * 100 / total
        speed = current / diff
        elapsed_time = round(diff) * 1000
        time_to_completion = round((total - current) / speed) * 1000
        estimated_total_time = elapsed_time + time_to_completion

        elapsed_time = TimeFormatter(milliseconds=elapsed_time)
        estimated_total_time = TimeFormatter(milliseconds=estimated_total_time)

        progress = "[{0}{1}] \nPercentage : {2}%\n".format(
            ''.join(["█" for i in range(math.floor(percentage / 5))]),
            ''.join(["░" for i in range(20 - math.floor(percentage / 5))]),
            round(percentage, 2))

        tmp = progress + "{0} of {1}\nSpeed : {2}/s\nETA : {3}\n".format(
            humanbytes(current),
            humanbytes(total),
            humanbytes(speed),
            # elapsed_time if elapsed_time != '' else "0 s",
            estimated_total_time if estimated_total_time != '' else "0 s"
        )
        try:
            await message.edit(
                text="{}\n {}".format(
                    ud_type,
                    tmp
                )
            )
        except:
            pass


def humanbytes(size):
    # https://stackoverflow.com/a/49361727/4723940
    # 2**10 = 1024
    if not size:
        return ""
    power = 2**10
    n = 0
    Dic_powerN = {0: ' ', 1: 'Ki', 2: 'Mi', 3: 'Gi', 4: 'Ti'}
    while size > power:
        size /= power
        n += 1
    return str(round(size, 2)) + " " + Dic_powerN[n] + 'B'


def TimeFormatter(milliseconds: int) -> str:
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = ((str(days) + "d, ") if days else "") + \
        ((str(hours) + "h, ") if hours else "") + \
        ((str(minutes) + "m, ") if minutes else "") + \
        ((str(seconds) + "s, ") if seconds else "") + \
        ((str(milliseconds) + "ms, ") if milliseconds else "")
    return tmp[:-2]

@Sybot.on_message(filters.private & filters.command("start"))
async def start(bot, update):
    await update.reply_text(
        text=f"Hello {update.from_user.mention}, 👋\n\nJust send me a media & I'll generate screenshot.\n\nMade with ❤️ by @Sybots",
        disable_web_page_preview=True,
        reply_markup=InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("📨 Updates", url="https://t.me/sybots"),
                 InlineKeyboardButton("🗂 Source", url="https://github.com/reindears/shotsy")]
            ]
        )
    )

@Sybot.on_message(filters.private & filters.media)
async def generate_screen_shot(bot, update):

    if update.reply_to_message is None:
        download_location = DOWNLOAD_LOCATION + "/"
        a = await update.reply_text(
            text="Downloading",
            reply_to_message_id=update.message_id
        )
        c_time = time.time()
        the_real_download_location = await bot.download_media(
            message=update,
            file_name=download_location,
            progress=progress_for_pyrogram,
            progress_args=(
                "Downloading",
                a,
                c_time
            )
        )
        if the_real_download_location is not None:
            await bot.edit_message_text(
                text="Downloaded Successfully",
                chat_id=update.chat.id,
                message_id=a.message_id
            )
            tmp_directory_for_each_user = DOWNLOAD_LOCATION + "/" + str(update.from_user.id)
            if not os.path.isdir(tmp_directory_for_each_user):
                os.makedirs(tmp_directory_for_each_user)
            images = await generate_screen_shots(
                the_real_download_location,
                tmp_directory_for_each_user,
                False,
                DEF_WATER_MARK_FILE,
                5,
                9
            )
            await bot.edit_message_text(
                text="Uploading",
                chat_id=update.chat.id,
                message_id=a.message_id
            )
            media_album_p = []
            if images is not None:
                i = 0
                for image in images:
                    if os.path.exists(image):
                        if i == 0:
                            media_album_p.append(
                                InputMediaPhoto(
                                    media=image,
                                    parse_mode="html"
                                )
                            )
                        else:
                            media_album_p.append(
                                InputMediaPhoto(
                                    media=image
                                )
                            )
                        i = i + 1
            await bot.send_media_group(
                chat_id=update.chat.id,
                disable_notification=True,
                media=media_album_p
            )
            #
            try:
                shutil.rmtree(tmp_directory_for_each_user)
                os.remove(the_real_download_location)
            except:
                pass
            await bot.edit_message_text(
                text="Thanks for using @Shotsybbot",
                chat_id=update.chat.id,
                message_id=a.message_id,
                disable_web_page_preview=True
            )
    else:
        await bot.send_message(
            chat_id=update.chat.id,
            text="Send a media or video to get screenshots",
            reply_to_message_id=update.message_id
        )

Sybot.run()
