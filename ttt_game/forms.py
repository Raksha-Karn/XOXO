from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms


class SignUpForm(UserCreationForm):
    email = forms.EmailField(max_length=200, label="", widget=forms.TextInput(attrs={'placeholder': 'Enter Email', 'class': 'form-control'}))
    first_name = forms.CharField(max_length=100, label="", widget=forms.TextInput(attrs={'placeholder': 'Enter First Name', 'class': 'form-control'}))
    last_name = forms.CharField(max_length=100, label="", widget=forms.TextInput(attrs={'placeholder': 'Enter Last Name', 'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        
    def __init__(self, *args, **kwargs):
        super(SignUpForm, self).__init__(*args, **kwargs)
        
        self.fields['username'].widget.attrs['class'] = 'form-control'
        self.fields['username'].widget.attrs['placeholder'] = 'Username'
        self.fields['username'].widget.attrs['label'] = ''
        self.fields['username'].widget.attrs['help_text'] = '<span class="form-text text-muted"><small>Required. 150 characters or fewer, letters, digits and @/./+/-/_ only.</small></span>'
        
        self.fields['password1'].widget.attrs['class'] = 'form-control'
        self.fields['password1'].widget.attrs['placeholder'] = 'Password'
        self.fields['password1'].widget.attrs['label'] = ''
        self.fields['password1'].widget.attrs['help_text'] = '<ul class="form-text text-muted small"><li>Required. Your password cannot be too small. It must contain at least 8 characters.</li><li>Must contain at least one uppercase letter, one lowercase letter, and one number</li></ul>'
        
        self.fields['password2'].widget.attrs['class'] = 'form-control'
        self.fields['password2'].widget.attrs['placeholder'] = 'Confirm Password'
        self.fields['password2'].widget.attrs['label'] = ''
        self.fields['password2'].widget.attrs['help_text'] = '<span class="form-text text-muted"><small>Enter the same password as before for verification.</small></span>'