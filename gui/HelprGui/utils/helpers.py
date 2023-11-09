import numpy as np
from datetime import datetime
from pathlib import Path


def hround(x, p=5):
    """Returns rounded value:
        if decimal, round to 5 significant digits
        if non-decimal, round to 4 decimal places

    References:
        https://stackoverflow.com/a/59888924/875127

    """
    if np.abs(x) < 1:
        x = np.asarray(x)
        x_positive = np.where(np.isfinite(x) & (x != 0), np.abs(x), 10 ** (p - 1))
        mags = 10 ** (p - 1 - np.floor(np.log10(x_positive)))
        return np.round(x * mags) / mags

    else:
        return np.round(x, p)


def init_session_dir(parent_dir=None):
    """ Creates directory for logs and output files. """
    started_at = datetime.now()
    session_dirname = started_at.strftime('HELPR/session_%Y-%m-%d_%H-%M-%S')
    if parent_dir is None:
        parent_dir = Path.cwd()
    session_dir = parent_dir.joinpath(session_dirname)
    Path.mkdir(session_dir, parents=True, exist_ok=True)
    return session_dir
