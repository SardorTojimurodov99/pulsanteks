{% extends "base.html" %}

{% block title %}{{ title }}{% endblock %}

{% block content %}
<h1>{{ title }}</h1>

<form method="post">
    {% csrf_token %}

    <div class="card">
        <h3>Jo'natma ma'lumotlari</h3>
        {{ form.as_p }}
    </div>

    <div class="card">
        <h3>Jo'natma qatorlari</h3>
        {{ formset.management_form }}
        {% for subform in formset %}
            <div style="border:1px solid #ddd; padding:12px; margin-bottom:12px; border-radius:8px;">
                {{ subform.as_p }}
            </div>
        {% endfor %}
    </div>

    <button class="btn" type="submit">Saqlash</button>
    <a class="btn btn-secondary" href="{% url 'shipment_list' %}">Bekor qilish</a>
</form>
{% endblock %}