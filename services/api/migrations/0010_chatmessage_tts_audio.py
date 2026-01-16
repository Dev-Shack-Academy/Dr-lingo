# Generated migration for TTS audio field

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("api", "0009_knowledge_bases_m2m"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatmessage",
            name="tts_audio",
            field=models.FileField(
                blank=True,
                help_text="Generated TTS audio for translation",
                null=True,
                upload_to="tts_audio/",
            ),
        ),
    ]
