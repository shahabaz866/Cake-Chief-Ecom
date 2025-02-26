from django import template



register = template.Library()

@register.filter(name='temp_tags')

def tags(list_data,tag_size):
    tag=[]
    i=0
    for j in list_data:
        tag.append(j)
        i = i+1
        if i== tag_size:
            yield tag
            i = 0 
            tag=[]

    if tag :
        yield tag

