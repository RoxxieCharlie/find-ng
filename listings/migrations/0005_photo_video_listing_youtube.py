from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('listings', '0004_alter_listing_price'),  # replace with your actual last migration name
    ]

    operations = [
        # Make price optional on Listing
        migrations.AlterField(
            model_name='listing',
            name='price',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True),
        ),
        # Add youtube_url to Listing
        migrations.AddField(
            model_name='listing',
            name='youtube_url',
            field=models.URLField(blank=True, help_text='YouTube video URL for this business (e.g. https://www.youtube.com/watch?v=abc123)'),
        ),
        # Add media_type to Photo
        migrations.AddField(
            model_name='photo',
            name='media_type',
            field=models.CharField(
                choices=[('image', 'Image'), ('video', 'Video')],
                default='image',
                max_length=10,
            ),
        ),
        # Add video_url to Photo
        migrations.AddField(
            model_name='photo',
            name='video_url',
            field=models.URLField(blank=True, help_text='YouTube video URL for gallery (images: leave blank)'),
        ),
        # Make image field optional on Photo
        migrations.AlterField(
            model_name='photo',
            name='image',
            field=models.ImageField(blank=True, null=True, upload_to='listings/photos/'),
        ),
    ]