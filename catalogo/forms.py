from django import forms
from .models import ConsultaCliente, Producto

class ConsultaClienteForm(forms.ModelForm):
    mensaje = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'apple-input',
            'rows': 4,
            'placeholder': 'Escribe tu consulta aquí (mínimo 15 caracteres)...',
        }), 
        min_length=15, 
        error_messages={'min_length': 'El mensaje debe tener al menos 15 caracteres.'}
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['productoInteres'].queryset = Producto.objects.filter(activo=True)
        self.fields['productoInteres'].required = False
        self.fields['productoInteres'].empty_label = 'Ninguno (Consulta general)'
        self.fields['productoInteres'].widget.attrs.update({'class': 'apple-input'})
        self.fields['nombre'].widget.attrs.update({
            'class': 'apple-input',
            'placeholder': 'Tu nombre completo',
        })
        self.fields['email'].widget.attrs.update({
            'class': 'apple-input',
            'placeholder': 'tucorreo@ejemplo.com',
        })

    class Meta:
        model = ConsultaCliente
        fields = ['nombre', 'email', 'mensaje', 'productoInteres']
