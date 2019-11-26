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
    fullName = models.CharField(max_length=300, null=False)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.TextField()
    startTime = models.DateTimeField(default=timezone.now, null=False)
    endTime = models.DateTimeField(default=timezone.now, null=False)
    status = models.SmallIntegerField(choices=asset_status, default=0)
    isPrivate = models.BooleanField(default=True)
    isAnonymous = models.BooleanField(default=True)
    cryptoMethod = models.SmallIntegerField(choices=asset_crypto_method, default=0)
    questions = models.TextField()
    selections = models.TextField()
    isAllowAbstention = models.BooleanField(default=False)
    publicKey = models.CharField(max_length=300, null=True)
    verifyFile = models.CharField(max_length=300, null=True)
    voteResult = models.CharField(max_length=300, null=True)

    # class Meta:
    #     ordering = ("-startTime",)

    def __str__(self):
        return self.shortName

    def to_dict(self):
        data = {}
        data['shortname'] = self.shortName
        data['fullname'] = self.fullName
        data['isprivate'] = self.isPrivate
        data['isanonymous'] = self.isAnonymous
        data['info'] = self.description
        data['starttime'] = self.startTime.strftime('%Y-%m-%d %H:%M:%S') if self.startTime else None
        data['endtime'] = self.endTime.strftime('%Y-%m-%d %H:%M:%S') if self.endTime else None

        data['questionlist'] = self.shortName.split('@')
        data['selectionlist'] = [each.split('&') for each in self.shortName.split('@')[1:]]
        data['voterslist'] = TempVoterList.objects.filter(election=self).value_list('voter')
        data['emaillist'] = TempVoterList.objects.filter(election=self).value_list('email')

        return data

    def update(self, data):
        self.shortName = data['shortname']
        self.fullName = data['fullname']
        self.isPrivate = data['isprivate']
        self.isAnonymous = data['isanonymous']
        self.description = data['info']
        self.startTime = data['starttime']
        self.endTime = data['endtime']

        question = data['questionlist'][0]
        for i in range(len(data['questionlist'] - 1)):
            question = question + "@" + data['questionlist'][i + 1]
        self.questions = question

        selections = ""
        for item in data['selectionlist']:
            selection = item[0]
            for i in range(len(item - 1)):
                selection = selection + "&" + item[i + 1]
            selections = selections + "@" + selection
        self.selections = selections

        self.save()

    @staticmethod
    def from_dict(data, user):
        election = {}
        election['author'] = user
        election['shortName'] = data['shortname']
        election['name'] = data['fullname']
        election['description'] = data['info']
        election['startTime'] = data['starttime']
        election['endTime'] = data['endtime']
        election['status'] = 0
        election['isPrivate'] = data['isprivate']
        election['isAnonymous'] = data['isanonymous']
        election['cryptoMethod'] = data['isanonymous']

        question = data['questionlist'][0]
        for i in range(len(data['questionlist'] - 1)):
            question = question + "@" + data['questionlist'][i + 1]
        election['questions'] = question

        selections = ""
        for item in data['selectionlist']:
            selection = item[0]
            for i in range(len(item - 1)):
                selection = selection + "&" + item[i + 1]
            selections = selections + "@" + selection
        election['selections'] = selections
        return Elections.objects.create(**election)


class VoterList(models.Model):
    voter = models.ForeignKey(User, on_delete=models.CASCADE)
    email = models.CharField(max_length=300, null=False)
    voteResult = models.CharField(max_length=300, null=True)
    voterKey = models.CharField(max_length=300, null=True)
    election = models.ForeignKey('Elections', on_delete=models.CASCADE)

    class Meta:
        ordering = ("voter",)

    def __str__(self):
        return self.voter


class TempVoterList(models.Model):
    voter = models.CharField(max_length=300, null=False)
    email = models.CharField(max_length=300, null=False)
    election = models.ForeignKey('Elections', on_delete=models.CASCADE)

    class Meta:
        ordering = ("voter",)

    def __str__(self):
        return self.voter


