from django.db import models
from django.utils import timezone
import os
from datetime import datetime
import pytz

# Múi giờ Hồ Chí Minh
HO_CHI_MINH_TZ = pytz.timezone('Asia/Ho_Chi_Minh')


def get_current_time():
    """Lấy thời gian hiện tại theo múi giờ Hồ Chí Minh."""
    return timezone.localtime(timezone.now(), HO_CHI_MINH_TZ)

class User(models.Model):
    """Model lưu thông tin người dùng (chỉ 1 user local)"""
    name = models.CharField(max_length=255, verbose_name="Tên người dùng")
    created_at = models.DateTimeField(default=get_current_time, verbose_name="Ngày tạo")
    updated_at = models.DateTimeField(default=get_current_time, verbose_name="Ngày cập nhật")
    
    class Meta:
        verbose_name = "Người dùng"
        verbose_name_plural = "Người dùng"
    
    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.pk and not self.created_at:
            self.created_at = get_current_time()
        self.updated_at = get_current_time()
        super().save(*args, **kwargs)
    
    def get_created_at_local(self):
        """Lấy thời gian tạo theo múi giờ Hồ Chí Minh"""
        return self.created_at.astimezone(HO_CHI_MINH_TZ)
    
    def get_updated_at_local(self):
        """Lấy thời gian cập nhật theo múi giờ Hồ Chí Minh"""
        return self.updated_at.astimezone(HO_CHI_MINH_TZ)


class Conversation(models.Model):
    """Model lưu đoạn hội thoại"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations', verbose_name="Người dùng")
    title = models.CharField(max_length=255, verbose_name="Tiêu đề hội thoại")
    last_question = models.TextField(blank=True, null=True, verbose_name="Câu hỏi cuối cùng")
    last_updated = models.DateTimeField(default=get_current_time, verbose_name="Cập nhật lần cuối")
    created_at = models.DateTimeField(default=get_current_time, verbose_name="Ngày tạo")
    total_messages = models.IntegerField(default=0, verbose_name="Tổng số tin nhắn")
    total_documents = models.IntegerField(default=0, verbose_name="Tổng số tài liệu")
    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")
    
    class Meta:
        verbose_name = "Đoạn hội thoại"
        verbose_name_plural = "Đoạn hội thoại"
        ordering = ['-last_updated']
    
    def __str__(self):
        return f"{self.title} - {self.user.name}"

    def save(self, *args, **kwargs):
        if not self.pk and not self.created_at:
            self.created_at = get_current_time()
        self.last_updated = get_current_time()
        super().save(*args, **kwargs)
    
    def get_created_at_local(self):
        """Lấy thời gian tạo theo múi giờ Hồ Chí Minh"""
        return self.created_at.astimezone(HO_CHI_MINH_TZ)
    
    def get_last_updated_local(self):
        """Lấy thời gian cập nhật cuối theo múi giờ Hồ Chí Minh"""
        return self.last_updated.astimezone(HO_CHI_MINH_TZ)


class Document(models.Model):
    """Model lưu thông tin tài liệu PDF"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='documents', verbose_name="Hội thoại")
    file_name = models.CharField(max_length=255, verbose_name="Tên file")
    file_path = models.CharField(max_length=500, verbose_name="Đường dẫn file")
    file_size = models.IntegerField(verbose_name="Kích thước (bytes)")
    uploaded_at = models.DateTimeField(default=get_current_time, verbose_name="Ngày upload")
    is_active = models.BooleanField(default=True, verbose_name="Đang hoạt động")
    
    class Meta:
        verbose_name = "Tài liệu"
        verbose_name_plural = "Tài liệu"
        ordering = ['-uploaded_at']
    
    def __str__(self):
        return self.file_name

    def save(self, *args, **kwargs):
        if not self.pk and not self.uploaded_at:
            self.uploaded_at = get_current_time()
        super().save(*args, **kwargs)
    
    def get_uploaded_at_local(self):
        """Lấy thời gian upload theo múi giờ Hồ Chí Minh"""
        return self.uploaded_at.astimezone(HO_CHI_MINH_TZ)


class Message(models.Model):
    """Model lưu lịch sử tin nhắn trong hội thoại"""
    ROLE_CHOICES = [
        ('user', 'Người dùng'),
        ('assistant', 'Trợ lý'),
    ]
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages', verbose_name="Hội thoại")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, verbose_name="Vai trò")
    content = models.TextField(verbose_name="Nội dung")
    timestamp = models.DateTimeField(default=get_current_time, verbose_name="Thời gian")
    
    class Meta:
        verbose_name = "Tin nhắn"
        verbose_name_plural = "Tin nhắn"
        ordering = ['timestamp']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."

    def save(self, *args, **kwargs):
        if not self.pk and not self.timestamp:
            self.timestamp = get_current_time()
        super().save(*args, **kwargs)
    
    def get_timestamp_local(self):
        """Lấy thời gian theo múi giờ Hồ Chí Minh"""
        return self.timestamp.astimezone(HO_CHI_MINH_TZ)


class QuestionHistory(models.Model):
    """Model lưu lịch sử câu hỏi để hiển thị sidebar"""
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='questions', verbose_name="Hội thoại")
    question = models.TextField(verbose_name="Câu hỏi")
    timestamp = models.DateTimeField(default=get_current_time, verbose_name="Thời gian hỏi")
    
    class Meta:
        verbose_name = "Lịch sử câu hỏi"
        verbose_name_plural = "Lịch sử câu hỏi"
        ordering = ['-timestamp']
    
    def __str__(self):
        return self.question[:50]

    def save(self, *args, **kwargs):
        if not self.pk and not self.timestamp:
            self.timestamp = get_current_time()
        super().save(*args, **kwargs)
    
    def get_timestamp_local(self):
        """Lấy thời gian theo múi giờ Hồ Chí Minh"""
        return self.timestamp.astimezone(HO_CHI_MINH_TZ)