import postcss from 'postcss';
import tailwindcss from 'tailwindcss';

export default {
  plugins: [
    tailwindcss(),
    postcss(),
  ],
};
