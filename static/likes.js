const likeBtns = document.querySelectorAll('button.btn.btn-sm');

for (btn of likeBtns) {
    btn.addEventListener('click', async (e) => {
        e.preventDefault()
        try {
            // Grab the button so we can have an id
            const button = e.target.matches('button.btn.btn-sm') ? e.target: e.target.parentNode

            const res = await axios.post(`/messages/${button.id}/like`);

            if (res.status === 200) {
                if (res.data.like_status === true) {
                    // We are liking a post
                    button.classList.toggle('btn-secondary');
                    button.classList.toggle('btn-primary');
                } else {
                    // We are removing like from post
                    button.classList.toggle('btn-primary');
                    button.classList.toggle('btn-secondary');

                }
        }
            } catch (error) {

            if (error.response.status === 403) {
                await flash(error.response.data.warning, 'danger');
            }

        }



    })
}

async function flash(message, category) {
    // We get the flash messages div
    const container = document.querySelector('div.container');

    // We create a div
    const m = document.createElement('div');
    m.className = (`alert alert-${category}`);
    m.innerText = message;

    container.prepend(m)
}