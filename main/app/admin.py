from django.contrib import admin
from app.models import Article, Category, ContentImage, ArticleImage ,ArticleImageCrop, ArticleImageType, StaffProfile

class ArticleAdmin(admin.ModelAdmin):
    pass

class CategoryAdmin(admin.ModelAdmin):
    pass

class FileAdmin(admin.ModelAdmin):
    pass

class ArticleImageAdmin(admin.ModelAdmin):
    pass

class ArticleImageCropAdmin(admin.ModelAdmin):
    pass

class ArticleImageTypeAdmin(admin.ModelAdmin):
    pass

class StaffProfileAdmin(admin.ModelAdmin):
    pass

admin.site.register(Article, ArticleAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(ContentImage, FileAdmin)
admin.site.register(ArticleImage, ArticleImageAdmin)
admin.site.register(ArticleImageCrop, ArticleImageCropAdmin)
admin.site.register(ArticleImageType, ArticleImageTypeAdmin)
admin.site.register(StaffProfile, StaffProfileAdmin)

