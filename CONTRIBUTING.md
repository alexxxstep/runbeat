# Contributing to RunBeat

Thank you for considering contributing to RunBeat! This document provides guidelines and information for contributors.

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- Node.js 18+
- Git
- Supabase account (for database)
- Spotify Developer account
- OpenAI API key

### Local Development Setup

1. **Clone the repository**
```bash
git clone https://github.com/your-org/runbeat.git
cd runbeat
```

2. **Backend Setup**
```bash
cd apps/backend
pip install -r requirements.txt
cp .env.example .env
# Fill in .env with your credentials
uvicorn app.main:app --reload
```

3. **Web Frontend Setup**
```bash
cd apps/web
npm install
cp .env.example .env
# Fill in .env
npm run dev
```

4. **Mobile App Setup** (optional)
```bash
cd apps/mobile
npm install
cp .env.example .env
# Fill in .env
npx expo start
```

## 📁 Project Structure

```
runbeat/
├── apps/
│   ├── backend/          # FastAPI Python backend
│   │   ├── app/
│   │   │   ├── agents/   # LangChain AI agents
│   │   │   ├── api/      # API routes
│   │   │   ├── services/ # Business logic
│   │   │   └── models/   # Data models
│   │   └── tests/        # Backend tests
│   ├── web/              # React + Vite web app
│   │   └── src/
│   │       ├── components/
│   │       ├── pages/
│   │       └── services/
│   └── mobile/           # React Native + Expo app
│       └── src/
├── docs/                 # Documentation
└── README.md
```

## 🔧 Development Workflow

### Branch Strategy
- `main` - Production-ready code
- `develop` - Integration branch for features
- `feature/feature-name` - New features
- `fix/bug-name` - Bug fixes
- `docs/description` - Documentation updates

### Making Changes

1. **Create a feature branch**
```bash
git checkout -b feature/your-feature-name
```

2. **Make your changes**
- Write clean, documented code
- Follow existing code style
- Add tests for new features
- Update documentation if needed

3. **Test your changes**
```bash
# Backend tests
cd apps/backend
pytest

# Frontend tests
cd apps/web
npm run test

# Linting
cd apps/backend
ruff check app/
black app/ --check

cd apps/web
npm run lint
```

4. **Commit your changes**
```bash
git add .
git commit -m "feat: add new feature description"
```

Use conventional commits:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting)
- `refactor:` - Code refactoring
- `test:` - Adding tests
- `chore:` - Maintenance tasks

5. **Push and create Pull Request**
```bash
git push origin feature/your-feature-name
```

## 📋 Code Style Guidelines

### Python (Backend)
- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use `black` for formatting
- Use `ruff` for linting

```python
# Good
def create_workout(
    user_id: str,
    workout_type: str,
    duration_minutes: int
) -> Dict[str, Any]:
    """
    Create a new workout for the user.

    Args:
        user_id: User's unique identifier
        workout_type: Type of workout (steady, intervals, etc.)
        duration_minutes: Duration in minutes

    Returns:
        Created workout data
    """
    pass
```

### TypeScript (Frontend)
- Use TypeScript strict mode
- Functional components with hooks
- Named exports for components
- Use Tailwind CSS for styling

```typescript
// Good
interface WorkoutProps {
  workoutId: string;
  userId: string;
}

export function WorkoutCard({ workoutId, userId }: WorkoutProps) {
  const [workout, setWorkout] = useState<Workout | null>(null);

  // Component logic
}
```

### React Components
- Keep components small and focused
- Extract reusable logic into custom hooks
- Use proper TypeScript types
- Follow naming conventions:
  - Components: PascalCase (`WorkoutCard`)
  - Hooks: camelCase with `use` prefix (`useWorkout`)
  - Utils: camelCase (`formatDuration`)

## 🧪 Testing

### Backend Tests
```bash
cd apps/backend
pytest tests/
pytest tests/test_specific.py -v
```

### Frontend Tests
```bash
cd apps/web
npm run test
npm run test:coverage
```

### Test Coverage
- Aim for >80% coverage on new code
- Write unit tests for business logic
- Write integration tests for API endpoints
- Write E2E tests for critical user flows

## 📚 Documentation

### Code Documentation
- Add docstrings to all functions/classes (Python)
- Add JSDoc comments for complex functions (TypeScript)
- Document API endpoints in OpenAPI format
- Update README.md for significant changes

### Architecture Documentation
Update relevant documentation files:
- `docs/ARCHITECTURE_REPORT.md` - System architecture
- `CHANGELOG.md` - Version changes
- Component-specific README files

## 🐛 Reporting Issues

### Bug Reports
Include:
- Clear title and description
- Steps to reproduce
- Expected vs actual behavior
- Screenshots/logs if applicable
- Environment details (OS, browser, versions)

### Feature Requests
Include:
- Use case and motivation
- Proposed solution
- Alternative solutions considered
- Impact on existing features

## 🔍 Code Review Process

1. **Self-review** - Review your own code first
2. **Automated checks** - Ensure CI passes
3. **Peer review** - Wait for at least one approval
4. **Address feedback** - Make requested changes
5. **Merge** - Squash and merge when approved

### Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass and coverage is adequate
- [ ] Documentation is updated
- [ ] No console.log or debug code
- [ ] Error handling is proper
- [ ] Performance considerations addressed
- [ ] Security implications reviewed

## 🚀 Release Process

1. Update version in relevant files
2. Update `CHANGELOG.md`
3. Create release branch
4. Tag release: `git tag v3.x.x`
5. Deploy to staging
6. Test on staging
7. Deploy to production
8. Announce release

## 💬 Communication

- **GitHub Issues** - Bug reports, feature requests
- **GitHub Discussions** - General questions, ideas
- **Pull Requests** - Code reviews, discussions

## 📝 License

By contributing to RunBeat, you agree that your contributions will be licensed under the same license as the project.

## 🙏 Thank You!

Your contributions make RunBeat better for everyone. We appreciate your time and effort!

---

**Questions?** Feel free to open an issue or start a discussion.

