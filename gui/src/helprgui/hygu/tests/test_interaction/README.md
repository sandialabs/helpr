# QML Component Interaction Tests

QML tests that verify UI components correctly interact with Python backend models via Qt bindings.

## Running Tests

```bash
cd repo/gui/src/helprgui/hygu/tests/test_interaction

# Run all tests (headless)
python run_qml_tests.py --all

# Run specific test file
python run_qml_tests.py --test test_float_param_field.qml

# Run with visible window (for debugging)
python run_qml_tests.py --test test_float_param_field.qml --visible

# Run via pytest
pytest test_qml_components.py -v
```

**Exit codes:** `0` = passed, `1` = failed

## Test Coverage

| Test File | Coverage |
|-----------|----------|
| `test_uncertain_param_field.qml` | Distribution switching, field visibility, validation |
| `test_float_param_field.qml` | Value changes, unit types, min/max values |
| `test_param_fields.qml` | IntField, BoolField, ChoiceField, StringField |
| `test_num_list_param_field.qml` | List values, parsing, min/max |
| `test_float_nullable_param_field.qml` | Nullable floats, null state transitions |
| `test_readonly_parameter.qml` | Read-only display, computed values |
| `test_file_selector.qml` | File path display, value changes |
| `test_directory_selector.qml` | Directory path display, value changes |

## Directory Structure

```
test_interaction/
├── run_qml_tests.py         # Test runner
├── qml_test_helper.py       # Python backend for tests
├── test_qml_components.py   # Pytest wrapper
├── Globals.qml              # Singleton with shared UI properties
├── qmldir                   # QML module definition
├── test_*.qml               # Test files
└── README.md
```

## Adding New Tests

### 1. Add Python support in `qml_test_helper.py`

```python
@Slot(result=QObject)
def create_your_field(self) -> YourFormField:
    return self._create_your_field(label="Test", value=42)

@Slot(result=str)
def get_your_value(self) -> str:
    return str(self._your_field.value) if self._your_field else ""
```

### 2. Create `test_your_component.qml`

Key requirements:
- Use `ApplicationWindow` as root with `visible: true`
- Import `"."` for `Globals` singleton
- Bind global properties to `Globals` (see existing test files)
- Use `Loader` with null checks for components
- Use timer-based test runner (150ms+ intervals)

### 3. Update `test_qml_components.py`

Add to `expected_tests` list.

See existing test files for complete examples.

## Key Patterns

**Globals singleton** - Centralizes UI constants:
```qml
import "."
property string color_primary: Globals.color_primary
```

**Null safety** - Prevents startup/shutdown errors:
```qml
Loader {
    active: tester !== null && tester.field !== null
    sourceComponent: YourComponent { param: tester ? tester.field : null }
}
```

**Qt lifecycle** - Prevents "C++ object deleted" errors:
```python
self._old_fields.append(self._field)  # Keep old reference
self._field = NewField(...)
self._field.setParent(self)
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "C++ object already deleted" | Keep old field references in a list, set parent on new fields |
| "Cannot read property of null" | Add null checks in Loader's `active` property |
| Tests show 0/0 passed | Ensure `testFunctions` array is populated |
| Component not visible | Use `ApplicationWindow` with `visible: true` |
| Global property errors | Import `Globals` singleton, bind local properties |
