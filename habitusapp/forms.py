from datetime import date
from django import forms
from django.contrib.auth import authenticate
from django import forms
from django.contrib.auth.models import User, Group
from .models import Aluno, Exercicio
from django.core.exceptions import ValidationError

class EmailLoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise forms.ValidationError('Usuário com esse e-mail não existe.')

        user = authenticate(username=user.username, password=password)
        if user is None:
            raise forms.ValidationError('Email ou senha incorretos.')

        self.cleaned_data['user'] = user
        return self.cleaned_data

# 

class AlunoForm(forms.ModelForm):
    username = forms.CharField(label='Nome de usuário')
    email = forms.EmailField(label='E-mail')
    password = forms.CharField(widget=forms.PasswordInput, label='Senha')

    class Meta:
        model = Aluno
        fields = [
            'nome',
            'matricula',
            'cpf',
            'data_nasc',
            'telefone',
            'foto_perfil'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Estilização dos campos
        self.fields['nome'].widget.attrs.update({'placeholder': 'Insira o nome do aluno', 'class': 'form-input'})
        self.fields['matricula'].widget.attrs.update({'placeholder': 'Insira a matrícula', 'class': 'form-input'})
        self.fields['cpf'].widget.attrs.update({'placeholder': 'xxx.xxx.xxx-xx', 'class': 'form-input'})
        self.fields['data_nasc'].widget = forms.DateInput(attrs={'type': 'date', 'class': 'form-input'})
        self.fields['telefone'].widget.attrs.update({'placeholder': '(ddd) xxxxx-xxxx', 'class': 'form-input'})
        self.fields['foto_perfil'].widget.attrs.update({'class': 'form-file', 'style': 'display: none;', 'id': 'id_foto_perfil', 'accept': 'image/*', 'onchange': 'previewImagem()'})
        self.fields['username'].widget.attrs.update({'placeholder': 'Crie um nome de usuário', 'class': 'form-input'})
        self.fields['email'].widget.attrs.update({'placeholder': 'Insira o e-mail do aluno', 'class': 'form-input'})
        self.fields['password'].widget.attrs.update({'id': 'senha', 'placeholder': 'Crie uma senha com no mínimo 8 dígitos', 'required': 'required'
})

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError('Este nome de usuário já está em uso.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este e-mail já está em uso.')
        return email

    def clean_cpf(self):
        cpf = self.cleaned_data['cpf']
        if Aluno.objects.filter(cpf=cpf).exists():
            raise ValidationError('Este CPF já está cadastrado.')
        return cpf

    def clean_matricula(self):
        matricula = self.cleaned_data.get('matricula')

        # Se estiver vazio, tudo bem (é opcional)
        if not matricula:
            return None

        # Se informado, verificar duplicidade
        if Aluno.objects.filter(matricula=matricula).exists():
            raise ValidationError('Esta matrícula já está cadastrada.')

        return matricula


    def save(self, commit=True):
        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password']
        )
        grupo_aluno, _ = Group.objects.get_or_create(name='Aluno')
        user.groups.add(grupo_aluno)

        aluno = super().save(commit=False)
        aluno.user = user
        aluno.email = self.cleaned_data['email']
        if commit:
            aluno.save()
        return aluno


class AlunoEditForm(forms.ModelForm):
    class Meta:
        model = Aluno
        fields = ['nome', 'matricula','telefone', 'foto_perfil']
        widgets = {
            'data_nasc': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['nome'].widget.attrs.update({'placeholder': 'Nome do aluno', 'class': 'form-input'})
        self.fields['matricula'].widget.attrs.update({'placeholder': 'Matrícula (opcional)', 'class': 'form-input'})
        self.fields['telefone'].widget.attrs.update({'placeholder': '(ddd) xxxxx-xxxx (opcional)', 'class': 'form-input'})


    def clean_matricula(self):
        matricula = self.cleaned_data['matricula']
        if matricula:  # Só valida se não estiver vazio
            if Aluno.objects.filter(matricula=matricula).exclude(pk=self.instance.pk).exists():
                raise ValidationError('Esta matrícula já está cadastrada para outro aluno.')
        return matricula


from django import forms
from habitusapp.models import Noticia

class NoticiaForm(forms.ModelForm):
    class Meta:
        model = Noticia
        fields = ['categoria', 'descricao', 'imagem']
        widgets = {
            'descricao': forms.Textarea(attrs={
                'placeholder': 'Digite a descrição da notícia...',
                'rows': 5,
                'class': 'form-textarea'
            }),
            'categoria': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

from django import forms
from .models import Treino

class TreinoForm(forms.ModelForm):
    class Meta:
        model = Treino
        fields = ['nome', 'nivel', 'data_inicio', 'data_fim']
        widgets = {
            'data_inicio': forms.DateInput(attrs={'type': 'date'}),
            'data_fim': forms.DateInput(attrs={'type': 'date'}),
        }


from .models import Professor 
class ProfessorForm(forms.ModelForm):
    username = forms.CharField(
        label='Nome de usuário',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Digite o nome de usuário desejado'})
    )
    email = forms.EmailField(
        label='Email',
        required=True
    )
    password = forms.CharField(
        label='Senha',
        widget=forms.PasswordInput,
        required=True
    )
    cpf = forms.CharField(
        label='CPF', 
        max_length=14, 
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'xxx.xxx.xxx-xx'})
    ) 
    matricula = forms.CharField(
        label='Matricula', 
        max_length=20, 
        required=True
    ) 
    data_nasc = forms.DateField(label='Data de nascimento', widget=forms.DateInput(attrs={'type': 'date'}))
    
    
    class Meta:
        model = Professor
        fields = ['nome','username', 'password', 'email', 'password', 'telefone', 'foto_perfil','data_nasc', 'tipo_trabalho', 'data_admissao', 'inst_formacao']
        widgets = {
            'data_admissao': forms.DateInput(attrs={'type': 'date'}),
            'tipo_trabalho': forms.Select(),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Só tenta acessar o user se o professor já existir (edição)
        if self.instance and self.instance.pk and hasattr(self.instance, 'user') and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email

    def clean_username(self):
        username = self.cleaned_data['username']
      
      # Verifica se o username foi alterado
        if hasattr(self.instance, 'user') and self.instance.user and self.instance.user.username == username:
            return username  # Não mudou, não precisa validar
          
      # Verifica se o username já existe
        if User.objects.filter(username=username).exists():
            raise ValidationError('Este nome de usuário já está em uso. Por favor, escolha outro.')

        return username

    def clean_email(self):
        email = self.cleaned_data['email']
    
    # Verifica se o email foi alterado
        if hasattr(self.instance, 'user') and self.instance.user and self.instance.user.email == email:
            return email  # Não mudou, não precisa validar
        
    # Verifica se o email já existe
        if User.objects.filter(email=email).exists():
            raise ValidationError('Este email já está em uso. Por favor, utilize outro.')
    
        return email

    def clean_cpf(self):
        cpf = self.cleaned_data['cpf']
        if Professor.objects.filter(cpf=cpf).exists():
            raise ValidationError('Este CPF já está cadastrado.')
        return cpf

    def clean_matricula(self):
        matricula = self.cleaned_data['matricula']
        if Professor.objects.filter(matricula=matricula).exists():
            raise ValidationError('Esta matricula já está cadastrado.')
        return matricula
        

    
    def save(self, commit=True):
        username = self.cleaned_data.get('username')
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password')
        cpf = self.cleaned_data['cpf'] 
        matricula = self.cleaned_data['matricula'] 
        data_nasc = self.cleaned_data['data_nasc']
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        grupo_professor, _ = Group.objects.get_or_create(name='Professor')
        user.groups.add(grupo_professor)
        user.save()

        professor = super().save(commit=False)
        professor.user = user
        professor.email = email
        professor.cpf = cpf
        professor.data_nasc = data_nasc
        professor.matricula = matricula
        if commit:
            professor.save()
        return professor

    
class ProfessorEditForm(forms.ModelForm):
    username = forms.CharField(
        label='Nome de usuário',
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Digite o nome de usuário desejado'})
    )
    email = forms.EmailField(
        label='Email',
        required=True
    )
    class Meta:
        model = Professor

        # Liste aqui apenas os campos que podem ser editados
        fields = [
            'nome',
            'telefone',
            'username',
            'email',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        professor = super().save(commit=False)
        user = professor.user
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            professor.save()
        return professor


class ExercicioForm(forms.ModelForm):
    class Meta:
        model = Exercicio
        fields = ['video', 'imagem','nome', 'grupo_muscular', 'dificuldade', 'descricao']
        widgets = {
            'nome': forms.TextInput(attrs={
                'placeholder': 'Digite o nome do exercício',
                'class': 'form-input'
            }),
            'grupo_muscular': forms.Select(attrs={
                'placeholder': 'Selecione o grupo muscular',
                'class': 'form-select'
            }),
            'dificuldade': forms.Select(attrs={
                'placeholder': 'Selecione o nível de dificuldade',
                'class': 'form-select'
            }),
            'descricao': forms.Textarea(attrs={
                'placeholder': 'Descreva como executar o exercício...',
                'rows': 10,
                'class': 'form-textarea'
            }),
            'video': forms.FileInput(attrs={
                'placeholder': 'Insira um vídeo do exercício',
                'class': 'form-file'
            })
        }

from django import forms
from django.forms import inlineformset_factory
from habitusapp.models import Treino, TreinoExercicio

class TreinoFormEdit(forms.ModelForm):
    class Meta:
        model = Treino
        fields = ["nome", "data_inicio", "data_fim", "nivel"] 
        

class TreinoExercicioForm(forms.ModelForm):
    class Meta:
        model = TreinoExercicio
        fields = ["exercicio", "series", "repeticoes", "carga", "observacao"]
        widgets = {
            "exercicio": forms.HiddenInput(),
            "observacao": forms.TextInput(attrs={'placeholder': 'Insira observações se necessário sobre o exercício'})
        }

# Inline formset: conecta os TreinoExercicio ao Treino
TreinoExercicioFormSet = inlineformset_factory(
    Treino, TreinoExercicio,
    form=TreinoExercicioForm,
    extra=0,   # quantos formulários em branco para adicionar novos
    can_delete=True
)

from .models import Progresso

class ProgressoForm(forms.ModelForm):
    class Meta:
        model = Progresso
        exclude = ['usuario', 'progresso_valor', 'concluidos', 'dias_treinados', 'data_entrada']  # Remove data_entrada do formulário
        widgets = {
            'nivel': forms.Select(attrs={'class': 'form-select'}),
            'objetivo': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Torna TODOS os campos opcionais
        for field in self.fields:
            self.fields[field].required = False

        self.fields['nivel'].choices = [('', 'Selecione o nível (opcional)')] + list(Progresso.NivelChoices.choices)
        self.fields['objetivo'].choices = [('', 'Selecione o objetivo (opcional)')] + list(Progresso.ObjetivoChoices.choices)

        # Remove required dos selects
        self.fields['nivel'].widget.attrs.update({'class': 'form-select'})
        self.fields['objetivo'].widget.attrs.update({'class': 'form-select'})
        
        # Placeholders
        campos_cm = ['cintura', 'abdomen', 'torax', 'quadril', 'coxa_direita', 'coxa_esquerda',
                    'panturrilha_direita', 'panturrilha_esquerda', 'braco_direito', 'braco_esquerdo',
                    'tricipital', 'subescapular', 'axilar_media', 'suprailiaca', 'abdominal', 'coxa', 'panturrilha']
        
        for field in self.fields:
            if field in campos_cm:
                self.fields[field].widget.attrs.update({
                    'class': 'form-input',
                    'placeholder': 'cm (opcional)'
                })
            elif field == 'peso':
                self.fields[field].widget.attrs.update({
                    'class': 'form-input',
                    'placeholder': 'kg (opcional)'
                })
            elif field == 'altura':
                self.fields[field].widget.attrs.update({
                    'class': 'form-input',
                    'placeholder': 'cm (opcional)'
                })

from django import forms
from .models import SolicitacaoDeTreino

class SolicitacaoDeTreinoForm(forms.ModelForm):
    class Meta:
        model = SolicitacaoDeTreino
        fields = ['descricao']
        widgets = {
            'descricao': forms.Textarea(attrs={
                'placeholder': 'Digite uma descrição sobre a solicitação...',
                'rows': 6,
                'maxlength': 2000,
                'class': 'descricao-textarea'
            }),
        }


class ProfessorCadastroForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    # Mantemos o CharField para o formulário
    nome_completo = forms.CharField(max_length=150, label="Nome Completo")
    password = forms.CharField(widget=forms.PasswordInput())

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        
        # O segredo: Pegamos o 'nome_completo' e jogamos no 'first_name' do User
        user.first_name = self.cleaned_data.get('nome_completo')
        
        # Define a senha (use o password vindo do POST se você adicionou o campo)
        # Se não adicionou no form, pode usar uma padrão para teste:
        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)

        if commit:
            user.save()
        return user

