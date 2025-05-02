# Supplier Ranking Service

A Django-based web application that uses Q-learning algorithms to rank suppliers based on various performance metrics. This intelligent system learns from supplier interactions and performance data to optimize supplier selection for businesses.

## Features

- **Intelligent Supplier Ranking**: Utilizes reinforcement learning (Q-learning) to rank suppliers based on historical performance
- **Performance Metrics Tracking**: Monitor supplier performance across multiple dimensions
- **Data-Driven Decisions**: Make informed supplier selection decisions based on automated analysis
- **REST API**: Access ranking data and analytics through a comprehensive API
- **Admin Dashboard**: Manage suppliers and view performance analytics through a user-friendly interface

## Technology Stack

- **Backend**: Django 5.2
- **Database**: PostgreSQL
- **Machine Learning**: Q-learning implemented with NumPy and Pandas
- **Data Visualization**: Matplotlib

## Installation

### Prerequisites

- Python 3.9 or higher
- PostgreSQL
- Virtual environment (recommended)

### Setup Instructions

1. **Clone the repository**

   ```bash
   git clone https://github.com/IASSCMS/supplier-ranking-service.git
   cd supplier-ranking-service
   ```

2. **Create and activate a virtual environment**

   ```bash
   python -m venv venv
   
   # On Windows
   venv\Scripts\activate
   
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**

   ```bash
   cp .env.example .env
   ```

   Edit the `.env` file and replace placeholder values with your actual configuration:
   - Generate a new Django secret key:
     ```bash
     python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
     ```
   - Configure database settings
   - Set DEBUG mode appropriately

5. **Apply migrations**

   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create a superuser (admin)**

   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**

   ```bash
   python manage.py runserver
   ```

   Visit http://127.0.0.1:8000/ in your browser to access the application.

## Usage

### Admin Interface

Access the admin interface at http://127.0.0.1:8000/admin/ to:
- Manage suppliers
- View performance metrics
- Configure ranking parameters
- Monitor system learning

### API Endpoints

- `/api/suppliers/` - List all suppliers
- `/api/suppliers/{id}/` - Get specific supplier details
- `/api/rankings/` - Get current supplier rankings
- `/api/metrics/` - View performance metrics

## Q-Learning Algorithm

The supplier ranking service implements a reinforcement learning approach using Q-learning. The algorithm:

1. Evaluates supplier actions as states
2. Assigns rewards based on performance metrics
3. Updates Q-values to optimize future supplier selection
4. Ranks suppliers based on their Q-values

Key metrics used in the learning process include:
- Delivery time performance
- Quality consistency
- Price competitiveness
- Responsiveness
- Compliance with requirements

## Development

### Running Tests

```bash
pytest
```

### Code Style

This project follows PEP 8 style guidelines. To check code style:

```bash
flake8
```

## Deployment

For production deployment:

1. Set `DEBUG=False` in `.env`
2. Configure proper database settings
3. Set up a production-ready web server (e.g., Gunicorn)
4. Use a reverse proxy (e.g., Nginx)
5. Set up static files serving

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Django community for the excellent web framework
- Reinforcement learning resources and research papers on supplier evaluation