# Subir el proyecto a GitHub

```
cd neurolens
git init
git add .
git commit -m "Estructura MVC y base de datos"
git branch -M main
git remote add origin https://github.com/USUARIO/neurolens.git
git push -u origin main
```
Recomendaciones
- Cada integrante debe hacer commits propios desde su cuenta (`git config user.name` / `user.email`). El Parcial 3 pedía ≥13 commits de todos; es buena práctica repetirlo.
- Commits pequeños y con mensaje claro: "Agrega login", "Corrige aspect coronal", "Manual de usuario".
- No suban `datos/` (pesado) ni `neurolens.db`: ya están en `.gitignore`.
- Incluyan en la entrega el **link** del repositorio (público o con acceso al profesor).
