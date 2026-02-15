# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-02-15

### Changed

- Added support for Django 6.x by updating package compatibility constraints and classifiers

## [0.3.0] - 2025-09-27

### Added

- Added `ref` parameter support for tracking additional context in click logs (thanks @Mte90)
- Made target_url optional to support dynamic URL targeting via JavaScript
- Added comprehensive documentation and examples for JavaScript integration
- Support for dynamic URL redirection without predefined target URLs

### Changed

- TrackedLink.target_url field is now optional (blank=True, null=True)
- Enhanced README with detailed examples for dynamic tracking scenarios

## [0.2.0] - 2025-08-31

### Added

- Built-in geolocation functionality (replacing requests dependency)
- Built-in IP detection utilities (replacing django-ipware dependency)
- Optional rate limiting - can now be completely disabled

### Changed

- Rate limiting is now optional and can be disabled via `CLICKIFY_ENABLE_RATELIMIT = False`
- Improved performance by removing external API dependencies

### Removed

- Removed dependency on `django-ipware` package
- Removed dependency on `requests` package
- Removed mandatory rate limiting requirement

## [0.1.0] - 2025-08-28

### Added

- Initial release of django-clickify
- Click tracking functionality with IP address, user agent, and timestamp logging
- Geolocation support via external API (using requests package)
- Rate limiting functionality (mandatory)
- IP filtering with allowlists and blocklists
- Django Admin integration for managing tracked links
- Template tag support for traditional Django templates
- DRF API support for headless/JavaScript applications
- IP detection using django-ipware package

### Dependencies

- `django-ipware` for IP address detection
- `requests` for geolocation API calls
- `django-ratelimit` for rate limiting (mandatory)
