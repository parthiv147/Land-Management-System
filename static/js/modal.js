'use strict';

const overlay = document.querySelector('.overlay-popup');

const modal = document.querySelector('.modal');
const btnCloseModal = document.querySelector('.close-modal');
const btns = document.querySelectorAll('.notloged');

const openModal = function () {
	modal.classList.remove('hidden');
	overlay.classList.remove('hidden');
};

const closeModal = function () {
	modal.classList.add('hidden');
	overlay.classList.add('hidden');
};

btns.forEach(function (btn) {
	btn.addEventListener('click', function () {
		openModal();
	});
});

btnCloseModal.addEventListener('click', closeModal);
overlay.addEventListener('click', closeModal);

document.addEventListener('keydown', function (e) {
	// console.log(e.key);

	if (e.key === 'Escape' && !modal.classList.contains('hidden')) {
		closeModal();
	}
});

// ///////////////////////////////////////////

const sliderOverlay = document.querySelector('.overlay-popup');
const imageContainers = document.querySelectorAll('.imageContainer');
const sliderModal = document.querySelector('.slider-modal');
const sliderBtnCloseModal = document.querySelector('.slider-close-modal');

const sliderOpenModal = function () {
	sliderModal.classList.remove('hidden');
	sliderOverlay.classList.remove('hidden');
};

const sliderCloseModal = function () {
	sliderModal.classList.add('hidden');
	sliderOverlay.classList.add('hidden');
};

// Loop through each image container to open modal
imageContainers.forEach(function (container) {
	container.addEventListener('click', function () {
		const popupImages = document.querySelectorAll('.sliderImage');

		const image1URL = container.getAttribute('data-image1');
		const image2URL = container.getAttribute('data-image2');
		const image3URL = container.getAttribute('data-image3');

		// Set the popup image src attributes
		popupImages[0].src = image1URL;
		popupImages[1].src = image2URL;
		popupImages[2].src = image3URL;

		// Show the popup
		sliderOpenModal();
	});
});

// close slider modal
sliderBtnCloseModal.addEventListener('click', sliderCloseModal);

// Slider
const slider = function () {
	const slides = document.querySelectorAll('.slide');
	const btnLeft = document.querySelector('.slider__btn--left');
	const btnRight = document.querySelector('.slider__btn--right');
	const dotContainer = document.querySelector('.dots');

	let curSlide = 0;
	const maxSlide = slides.length;

	// Functions
	const createDots = function () {
		slides.forEach(function (_, i) {
			dotContainer.insertAdjacentHTML(
				'beforeend',
				`<button class="dots__dot" data-slide="${i}"></button>`
			);
		});
	};

	const activateDot = function (slide) {
		document
			.querySelectorAll('.dots__dot')
			.forEach((dot) => dot.classList.remove('dots__dot--active'));

		document
			.querySelector(`.dots__dot[data-slide="${slide}"]`)
			.classList.add('dots__dot--active');
	};

	const goToSlide = function (slide) {
		slides.forEach(
			(s, i) => (s.style.transform = `translateX(${100 * (i - slide)}%)`)
		);
	};

	// Next slide
	const nextSlide = function () {
		if (curSlide === maxSlide - 1) {
			curSlide = 0;
		} else {
			curSlide++;
		}

		goToSlide(curSlide);
		activateDot(curSlide);
	};

	const prevSlide = function () {
		if (curSlide === 0) {
			curSlide = maxSlide - 1;
		} else {
			curSlide--;
		}
		goToSlide(curSlide);
		activateDot(curSlide);
	};

	const init = function () {
		goToSlide(0);
		createDots();

		activateDot(0);
	};
	init();

	// Event handlers
	btnRight.addEventListener('click', nextSlide);
	btnLeft.addEventListener('click', prevSlide);

	document.addEventListener('keydown', function (e) {
		if (e.key === 'ArrowLeft') prevSlide();
		e.key === 'ArrowRight' && nextSlide();
	});

	dotContainer.addEventListener('click', function (e) {
		if (e.target.classList.contains('dots__dot')) {
			const { slide } = e.target.dataset;
			goToSlide(slide);
			activateDot(slide);
		}
	});
};
// calling slider function
slider();
