# Contributing to Helix Web OS

We welcome contributions! This is a community project built with passion.

## Getting Started

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Write tests for new functionality
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## Development Setup

```bash
# Backend
pip install -r requirements.txt
python -m pytest tests/

# Frontend
cd src/frontend
npm install
npm run dev
```

## Code Style

- **Python**: Follow PEP 8, use type hints
- **TypeScript**: Follow ESLint config, use strict mode
- **Documentation**: Write clear docstrings and comments

## Testing

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/
```

## Reporting Issues

Please use GitHub Issues to report bugs or suggest features.

## License

By contributing, you agree that your contributions will be licensed under the same dual-license model (Apache 2.0 + Proprietary Commercial).

---

Thank you for contributing to Helix Web OS!
