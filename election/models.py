from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models.fields import DateTimeField
from django.db.models.fields.related import ManyToManyField


class Elections(models.Model):
    asset_status = (
        (0, '未启动'),
        (1, '投票中'),
        (2, '冻结中'),
        (3, '验证中'),
        (4, '已完成'),
        (5, '已结束'),
        (6, '已废弃'),
    )
    asset_crypto_method = (
        (0, '不加密'),
        (1, '加密一'),
    )
    shortName = models.CharField(max_length=300, null=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=300, null=False)
    description = models.TextField()
    startTime = models.DateTimeField(default=timezone.now, null=False)
    endTime = models.DateTimeField(default=timezone.now, null=False)
    status = models.SmallIntegerField(choices=asset_status, default=0)
    isPrivate = models.BooleanField(default=True)
    isAnonymous = models.BooleanField(default=True)
    cryptoMethod = models.SmallIntegerField(choices=asset_crypto_method, default=0)
    question = models.CharField(max_length=300, null=True)
    selections = models.CharField(max_length=300, null=True)
    isAllowAbstention = models.BooleanField(default=False)
    publicKey = models.CharField(max_length=300, null=True)
    verifyFile = models.CharField(max_length=300, null=True)
    voteResult = models.CharField(max_length=300, null=True)

    class Meta:
        ordering = ("-startTime",)

    def __str__(self):
        return self.shortName

    def to_dict(self, fields=None, exclude=None):
        data = {}
        for f in self._meta.concrete_fields + self._meta.many_to_many:
            value = f.value_from_object(self)

            if fields and f.name not in fields:
                continue

            if exclude and f.name in exclude:
                continue

            if isinstance(f, ManyToManyField):
                value = [i.id for i in value] if self.pk else None

            if isinstance(f, DateTimeField):
                value = value.strftime('%Y-%m-%d %H:%M:%S') if value else None

            data[f.name] = value

        return data


class VoterList(models.Model):
    voter = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.CharField(max_length=300, null=False)
    voteResult = models.CharField(max_length=300, null=True)
    voterKey = models.CharField(max_length=300, null=True)
    Elections = models.ForeignKey('Elections', on_delete=models.CASCADE)

    class Meta:
        ordering = ("voter",)

    def __str__(self):
        return self.voter

