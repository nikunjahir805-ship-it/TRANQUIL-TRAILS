from django.db import migrations, models


def seed_testimonials(apps, schema_editor):
    Product = apps.get_model('core', 'Product')
    Customer = apps.get_model('core', 'Customer')
    Review = apps.get_model('core', 'Review')

    products = list(Product.objects.order_by('id'))
    if not products:
        return

    seeds = [
        {
            'name': 'Aarav Mehta',
            'email': 'aarav.mehta@example.com',
            'rating': 5,
            'comment': 'The handcrafted bowl arrived beautifully packed and instantly made the dining table feel warmer and more intentional.',
            'avatar': 'products/021209536c3ac73f84ba329d606cdc5a.jpg',
            'liked': True,
        },
        {
            'name': 'Saanvi Patel',
            'email': 'saanvi.patel@example.com',
            'rating': 5,
            'comment': 'Every detail feels thoughtful. The ceramic finish, the colors, and the calm presentation all match the brand perfectly.',
            'avatar': 'products/07903bf68490e7855c511fb2fb3f68db.jpg',
            'liked': True,
        },
        {
            'name': 'Kabir Shah',
            'email': 'kabir.shah@example.com',
            'rating': 5,
            'comment': 'I bought a piece for my study and ended up ordering two more. The work feels authentic, not mass-produced.',
            'avatar': 'products/0c6d72832122a63298fded2c99d8bb94.jpg',
            'liked': False,
        },
        {
            'name': 'Meera Joshi',
            'email': 'meera.joshi@example.com',
            'rating': 4,
            'comment': 'The textures are gorgeous and the whole shopping experience felt calm, clean, and easy to trust.',
            'avatar': 'products/1.jpeg',
            'liked': True,
        },
        {
            'name': 'Ishaan Verma',
            'email': 'ishaan.verma@example.com',
            'rating': 5,
            'comment': 'This store made it easy to find something meaningful for a gift. The product looked even better in person.',
            'avatar': 'products/119b63b9ab863e06cf5d6b961d06c933.jpg',
            'liked': False,
        },
        {
            'name': 'Diya Reddy',
            'email': 'diya.reddy@example.com',
            'rating': 5,
            'comment': 'I love how the piece adds a quiet, handmade character to the room without feeling overpowering.',
            'avatar': 'products/14f03e5ea82ca413bca08a1cb19424b2.jpg',
            'liked': True,
        },
        {
            'name': 'Rohan Kapoor',
            'email': 'rohan.kapoor@example.com',
            'rating': 5,
            'comment': 'Excellent quality, quick delivery, and the craftsmanship is obvious the moment you open the box.',
            'avatar': 'products/175cd24826ee22cc76e915576c759ba7.jpg',
            'liked': False,
        },
        {
            'name': 'Ananya Nair',
            'email': 'ananya.nair@example.com',
            'rating': 5,
            'comment': 'The handmade finish gave our living space exactly the kind of soft, natural feel we were looking for.',
            'avatar': 'products/1afafe6e86c62466519d3fcf9a5e52da.jpg',
            'liked': True,
        },
        {
            'name': 'Vedant Kulkarni',
            'email': 'vedant.kulkarni@example.com',
            'rating': 4,
            'comment': 'A very polished brand experience. The product images were accurate and the item was packaged with care.',
            'avatar': 'products/1f27c37f79ade576bccfcefece14b467.jpg',
            'liked': False,
        },
        {
            'name': 'Tara Singh',
            'email': 'tara.singh@example.com',
            'rating': 5,
            'comment': 'The woodwork feels timeless. It is the kind of piece that gets compliments every time someone visits.',
            'avatar': 'products/1f27c37f79ade576bccfcefece14b467_SHbAWwe.jpg',
            'liked': True,
        },
        {
            'name': 'Arjun Malhotra',
            'email': 'arjun.malhotra@example.com',
            'rating': 5,
            'comment': 'What stood out most was the balance of style and substance. Beautiful product, but also practical in daily use.',
            'avatar': 'products/1f7b17d5f8502093f8607fdf85bc22e5.jpg',
            'liked': False,
        },
        {
            'name': 'Nisha Bhat',
            'email': 'nisha.bhat@example.com',
            'rating': 5,
            'comment': 'I wanted something handcrafted for my entryway and this shop delivered exactly that mood.',
            'avatar': 'products/2164873d6cd7413f4dbd7d2c723612d0.jpg',
            'liked': True,
        },
        {
            'name': 'Dev Patel',
            'email': 'dev.patel@example.com',
            'rating': 5,
            'comment': 'The product feels like it belongs in a gallery, but it still works beautifully in a real home.',
            'avatar': 'products/244751fd57016b262051425302fe39da.jpg',
            'liked': False,
        },
        {
            'name': 'Kriti Rao',
            'email': 'kriti.rao@example.com',
            'rating': 5,
            'comment': 'I appreciate how consistent the brand feels from the website to the packaging to the piece itself.',
            'avatar': 'products/2574e8c5d5478576ed8aa5d0891ee869.jpg',
            'liked': True,
        },
        {
            'name': 'Siddharth Jain',
            'email': 'siddharth.jain@example.com',
            'rating': 4,
            'comment': 'The craftsmanship is strong and the ordering process was straightforward from start to finish.',
            'avatar': 'products/3.jpeg',
            'liked': False,
        },
        {
            'name': 'Pooja Iyer',
            'email': 'pooja.iyer@example.com',
            'rating': 5,
            'comment': 'A lovely reminder that handmade items can feel modern, elegant, and welcoming all at once.',
            'avatar': 'products/323fcdf46dc051b721e7de70e1c912b3.jpg',
            'liked': True,
        },
        {
            'name': 'Harsh Vyas',
            'email': 'harsh.vyas@example.com',
            'rating': 5,
            'comment': 'The tone of the store is peaceful and the products match that mood exactly. Very memorable.',
            'avatar': 'products/37a5ac987cddd5f2933762dfa48667f2.jpg',
            'liked': False,
        },
        {
            'name': 'Riya Chandra',
            'email': 'riya.chandra@example.com',
            'rating': 5,
            'comment': 'My order felt personal from beginning to end. That level of care is rare and appreciated.',
            'avatar': 'products/3d323caea3a062a813e8a30a426e4326.jpg',
            'liked': True,
        },
        {
            'name': 'Naveen Rao',
            'email': 'naveen.rao@example.com',
            'rating': 5,
            'comment': 'A great fit for anyone who wants thoughtful decor rather than something generic.',
            'avatar': 'products/41e03c3f0fad1d81c93ea406bc141dad.jpg',
            'liked': False,
        },
        {
            'name': 'Simran Kaur',
            'email': 'simran.kaur@example.com',
            'rating': 5,
            'comment': 'The avatar images and product presentation both make the whole brand feel polished and human.',
            'avatar': 'products/442427a46cde46a98d4c359c4ffd30a9.jpg',
            'liked': True,
        },
    ]

    for index, seed in enumerate(seeds):
        product = products[index % len(products)]
        customer, _ = Customer.objects.get_or_create(
            email=seed['email'],
            defaults={'full_name': seed['name']},
        )
        customer.full_name = seed['name']
        customer.save(update_fields=['full_name'])

        Review.objects.update_or_create(
            customer=customer,
            product=product,
            comment=seed['comment'],
            defaults={
                'rating': seed['rating'],
                'is_liked': seed['liked'],
                'avatar_image': seed['avatar'],
            },
        )


def reverse_seed_testimonials(apps, schema_editor):
    Review = apps.get_model('core', 'Review')
    Customer = apps.get_model('core', 'Customer')

    seed_emails = {
        'aarav.mehta@example.com',
        'saanvi.patel@example.com',
        'kabir.shah@example.com',
        'meera.joshi@example.com',
        'ishaan.verma@example.com',
        'diya.reddy@example.com',
        'rohan.kapoor@example.com',
        'ananya.nair@example.com',
        'vedant.kulkarni@example.com',
        'tara.singh@example.com',
        'arjun.malhotra@example.com',
        'nisha.bhat@example.com',
        'dev.patel@example.com',
        'kriti.rao@example.com',
        'siddharth.jain@example.com',
        'pooja.iyer@example.com',
        'harsh.vyas@example.com',
        'riya.chandra@example.com',
        'naveen.rao@example.com',
        'simran.kaur@example.com',
    }

    Review.objects.filter(customer__email__in=seed_emails).delete()
    Customer.objects.filter(email__in=seed_emails).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0011_sitesetting_footer_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='review',
            name='avatar_image',
            field=models.ImageField(blank=True, null=True, upload_to='reviews/avatars/'),
        ),
        migrations.RunPython(seed_testimonials, reverse_seed_testimonials),
    ]
