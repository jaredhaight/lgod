from django.contrib import admin
from app.models import Article, Category, ArticleImageUpload, ArticleImage, ArticleImageType

class ArticleAdmin(admin.ModelAdmin):
    pass

class CategoryAdmin(admin.ModelAdmin):
    pass

class FileAdmin(admin.ModelAdmin):
    pass

class ArticleImageAdmin(admin.ModelAdmin):
    pass

class ArticleImageTypeAdmin(admin.ModelAdmin):
    pass

admin.site.register(Article, ArticleAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(ArticleImageUpload, FileAdmin)
admin.site.register(ArticleImage, ArticleImageAdmin)
admin.site.register(ArticleImageType, ArticleImageTypeAdmin)

